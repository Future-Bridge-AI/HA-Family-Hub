"""LiveHA: boot a real Home Assistant over HTTPS in a temp config directory for live tests.

The Home Assistant comes from the sandbox harness venv ($HOME/.cache/fh-hassfest/venv, override
with FH_HASS). Nothing is installed: HA is started with --skip-pip, so an integration whose
requirement is missing fails loudly instead of being pip-installed. The integration is copied
(never imported in place) so no bytecode lands in the repository.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HASS = os.path.expandvars("$HOME/.cache/fh-hassfest/venv/bin/hass")
LEAF_IP = "192.168.50.10"

# Host values the seed applies to the instance (D-31); fixed so tests are deterministic.
HOST_ENV = {
    "TZ": "Europe/London",
    "HA_COUNTRY": "GB",
    "HA_CURRENCY": "GBP",
    "HA_UNIT_SYSTEM": "metric",
    "HA_LANGUAGE": "en",
}


class LiveHA:
    """Context manager that owns one temp dir and one HA process."""

    def __init__(self, target: str, port: int, integration_src: str = "custom_components/family_hub") -> None:
        self.target = target
        self.port = port
        self.integration_src = REPO_ROOT / integration_src
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-live-"))
        self.certs = self.tmp / "certs"
        self.config_dir = self.tmp / "config"
        self.secrets_dir = self.tmp / "secrets"
        self.log_path = self.tmp / "hass.log"
        self.base_url = "https://127.0.0.1:%d" % port
        self.ca = str(self.certs / "ca.crt")
        self.boot_seconds: Optional[float] = None
        self._proc: Optional[subprocess.Popen] = None
        self._stdout = None

    # -- lifecycle -------------------------------------------------------------------------------

    def __enter__(self) -> "LiveHA":
        try:
            self._prepare()
            self.start()
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.stop()
        if os.environ.get("FH_KEEP_LIVE") == "1":
            print("FH_KEEP_LIVE=1: kept %s" % self.tmp, file=sys.stderr)
            return
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _prepare(self) -> None:
        subprocess.run(
            [str(REPO_ROOT / "scripts" / "make-certs"), "--out", str(self.certs), "--ip", LEAF_IP],
            check=True,
            capture_output=True,
            text=True,
        )
        self.config_dir.mkdir(parents=True)
        template = (REPO_ROOT / "dev" / "config-template" / "configuration.yaml").read_text(encoding="utf-8")
        rendered = template.replace("/ssl/", "%s/" % self.certs)
        rendered = re.sub(r"^http:\s*$", "http:\n  server_port: %d" % self.port, rendered, flags=re.M)
        (self.config_dir / "configuration.yaml").write_text(rendered, encoding="utf-8")
        shutil.copytree(
            self.integration_src,
            self.config_dir / "custom_components" / "family_hub",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    def start(self) -> None:
        hass = os.environ.get("FH_HASS", DEFAULT_HASS)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        self._stdout = open(self.tmp / "hass.stdout", "ab")
        self._proc = subprocess.Popen(
            [hass, "-c", str(self.config_dir), "--log-file", str(self.log_path), "--skip-pip"],
            env=env,
            stdout=self._stdout,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        started = time.monotonic()
        result = self.seed("wait", timeout=300)
        if result.returncode != 0:
            raise RuntimeError("Home Assistant did not answer: %s\n%s" % (result.stderr, self.log_text()[-3000:]))
        self.boot_seconds = time.monotonic() - started

    def stop(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=10)
            except ProcessLookupError:
                pass
        if self._stdout is not None:
            self._stdout.close()
            self._stdout = None

    def restart(self) -> None:
        self.stop()
        self.start()

    # -- helpers ---------------------------------------------------------------------------------

    def log_text(self) -> str:
        try:
            return self.log_path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return ""

    def seed(
        self,
        *args: str,
        env: Optional[dict[str, str]] = None,
        target: Optional[str] = None,
        base_url: Optional[str] = None,
        ca: Optional[str] = None,
        timeout: float = 600,
    ) -> subprocess.CompletedProcess:
        """Run ``python -m tools.seed`` from the repo root; global options can be overridden."""
        command = [
            sys.executable,
            "-B",
            "-m",
            "tools.seed",
            "--target",
            target or self.target,
            "--base-url",
            base_url or self.base_url,
            "--ca",
            ca or self.ca,
            "--secrets-dir",
            str(self.secrets_dir),
            "--timeout",
            str(timeout),
            *args,
        ]
        return subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **HOST_ENV, **(env or {})),
            capture_output=True,
            text=True,
            timeout=timeout + 60,
        )

    def credentials(self, target: Optional[str] = None) -> dict:
        path = self.secrets_dir / ("credentials-%s.json" % (target or self.target))
        return json.loads(path.read_text(encoding="utf-8"))

    @contextlib.asynccontextmanager
    async def admin_session(self):
        """Yield ``(client, token, ws)`` logged in as the tool's admin (credentials already stored)."""
        from tools.seed.client import HAClient

        admin = self.credentials()["admin"]
        async with HAClient(self.base_url, self.ca) as client:
            token = await client.login(admin["username"], admin["password"])
            ws = await client.ws(token)
            yield client, token, ws

    @contextlib.asynccontextmanager
    async def admin_ws(self):
        """Yield an admin WebSocket (see admin_session for the REST client and token too)."""
        async with self.admin_session() as (_client, _token, ws):
            yield ws

    def run_async(self, coro: Any) -> Any:
        return asyncio.run(coro)
