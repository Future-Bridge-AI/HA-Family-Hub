"""Live tests: the seed tool against a real Home Assistant (one boot for the whole class).

Run: FH_HASS=$HOME/.cache/fh-hassfest/venv/bin/hass python -B -m unittest discover \
        -s tools/seed/tests -t . -p 'live_dev.py' -v
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import time
import unittest

from .live_ha import REPO_ROOT, LEAF_IP, LiveHA


class LiveDevTests(unittest.TestCase):
    ha: LiveHA
    first: subprocess.CompletedProcess

    @classmethod
    def setUpClass(cls) -> None:
        cls.ha = LiveHA("dev", 18130)
        cls.ha.__enter__()
        try:
            cls.first = cls.ha.seed("bootstrap")
        except BaseException:
            cls.ha.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ha.__exit__(None, None, None)

    def test_a_bootstrap_names_and_promotes_a_real_ha(self) -> None:
        self.assertEqual(self.first.returncode, 0, self.first.stderr)
        for line in ("onboarded", "http config promoted", "location_name = Family Hub DEV"):
            self.assertIn(line, self.first.stdout)

        async def read():
            async with self.ha.admin_ws() as ws:
                http = (await ws.call("http/config"))["result"]
                config = (await ws.call("get_config"))["result"]
            return http, config

        http, config = self.ha.run_async(read())
        self.assertEqual(http["active_config_type"], "stable")
        self.assertIsNone(http["revert_at"])
        self.assertEqual(config["location_name"], "Family Hub DEV")
        self.assertEqual(config["time_zone"], "Europe/London")
        self.assertEqual(config["version"], "2026.10.4")
        self.assertEqual(config["state"], "RUNNING")
        self.assertIn("custom integration family_hub", self.ha.log_text())

    def test_b_second_bootstrap_changes_nothing(self) -> None:
        path = self.ha.secrets_dir / "credentials-dev.json"
        before = path.read_bytes()
        second = self.ha.seed("bootstrap")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotIn("onboarded\n", second.stdout)
        self.assertEqual(path.read_bytes(), before)

        async def users():
            async with self.ha.admin_ws() as ws:
                return (await ws.call("config/auth/list"))["result"]

        # HA also lists its own system-generated "Home Assistant Content" user; people are the rest.
        listed = [u for u in self.ha.run_async(users()) if not u["system_generated"]]
        self.assertEqual([u["username"] for u in listed], ["fhtools"])

    def test_c_non_loopback_base_url_is_refused_before_connecting(self) -> None:
        started = time.monotonic()
        result = self.ha.seed("wait", base_url="https://192.0.2.10:8130")
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("loopback", result.stderr)

    def test_d_certificate_from_another_ca_fails_with_tls_error(self) -> None:
        other = self.ha.tmp / "other-certs"
        subprocess.run(
            [str(REPO_ROOT / "scripts" / "make-certs"), "--out", str(other), "--ip", LEAF_IP],
            check=True,
            capture_output=True,
        )
        result = self.ha.seed("wait", ca=str(other / "ca.crt"), timeout=20)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("TLS", result.stderr)

    def test_e_identity_guard_refuses_a_differently_named_instance(self) -> None:
        shutil.copyfile(
            self.ha.secrets_dir / "credentials-dev.json",
            self.ha.secrets_dir / "credentials-preview.json",
        )
        result = self.ha.seed("bootstrap", target="preview")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("Family Hub DEV", result.stderr)
        self.assertIn("Family Hub PREVIEW", result.stderr)

        async def name():
            async with self.ha.admin_ws() as ws:
                return (await ws.call("get_config"))["result"]["location_name"]

        self.assertEqual(self.ha.run_async(name()), "Family Hub DEV")

    def test_f_credentials_are_private(self) -> None:
        path = self.ha.secrets_dir / "credentials-dev.json"
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.ha.secrets_dir).st_mode), 0o700)


if __name__ == "__main__":
    unittest.main()
