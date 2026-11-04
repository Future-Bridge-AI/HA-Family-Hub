"""Live D-10 proof: the Google sign-in survives a reset (save, wipe, restore, credential, reload, loaded).

No Google account is involved. A synthetic Google config entry (fake token, valid for 30 days, so Home
Assistant never needs to refresh it) is written into a fresh harness config exactly as a reset writes it
back, and the application credential is the one the seed creates from a family file with a fake client id.
The Google Calendar platform then tries to list calendars with the fake token and fails; that is expected
and only logged. What is proved is the sign-in mechanics: state before and after the credential, the
saved file's mode, and the same entry loading again after the wipe.

One Home Assistant boot per class (port 18134, target dev).

Run: FH_HASS=$HOME/.cache/fh-hassfest/venv/bin/hass python -B -m unittest discover \
        -s tools/seed/tests -t . -p 'live_google.py' -v
"""
from __future__ import annotations

import datetime
import json
import os
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import yaml

from tools.seed import family_file

from .live_ha import REPO_ROOT, LiveHA

PORT = 18134
CLIENT_ID = "test-client.apps.googleusercontent.com"  # fake, never a real id
CLIENT_SECRET = "test-secret"
UNIQUE_ID = "test-primary@example.com"
ENTRY_ID = "01TESTGOOGLEENTRY000000000"
REFRESH_TOKEN = "y-refresh-token-for-the-synthetic-entry"
SIGNIN_TEXT = "Google sign-in is needed once for this environment"


def versions() -> tuple[int, int, int, int]:
    """(file version, file minor, entry version, entry minor) as Home Assistant 2026.10.4 itself declares them."""
    from homeassistant import config_entries
    from homeassistant.components.google import config_flow

    return (
        config_entries.STORAGE_VERSION,
        config_entries.STORAGE_VERSION_MINOR,
        config_flow.OAuth2FlowHandler.VERSION,
        config_flow.OAuth2FlowHandler.MINOR_VERSION,
    )


def implementation_id() -> str:
    """The id Home Assistant gives the application credential for CLIENT_ID (what a real sign-in stores)."""
    from homeassistant.util import slugify

    return slugify("google.%s" % CLIENT_ID)


def synthetic_core_config_entries() -> str:
    """A core.config_entries holding one signed-in Google entry (domain google, read/write, fake token)."""
    file_version, file_minor, entry_version, entry_minor = versions()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    expires = time.time() + 30 * 24 * 3600
    entry = {
        "created_at": now,
        "data": {
            "auth_implementation": implementation_id(),
            "token": {
                "access_token": "x",
                "refresh_token": REFRESH_TOKEN,
                "token_type": "Bearer",
                "scope": "https://www.googleapis.com/auth/calendar",
                "expires_in": 30 * 24 * 3600,
                "expires_at": expires,
            },
        },
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "google",
        "entry_id": ENTRY_ID,
        "minor_version": entry_minor,
        "modified_at": now,
        "options": {"calendar_access": "read_write"},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": UNIQUE_ID,
        "unique_id": UNIQUE_ID,
        "version": entry_version,
    }
    return json.dumps(
        {"version": file_version, "minor_version": file_minor, "key": "core.config_entries", "data": {"entries": [entry]}},
        indent=2,
    )


def write_family(path: Path) -> None:
    """The example family plus a google block with one calendar that is read-only and never gets events."""
    data = yaml.safe_load(family_file.EXAMPLE_FILE.read_text(encoding="utf-8"))
    data["google"] = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "calendars": [
            {
                "key": "primary",
                "calendar_id": UNIQUE_ID,
                "person": "Jordan",
                "writable": False,
                "expect_events": False,
                "backup": "ha-snapshot",
            }
        ],
    }
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


class LiveGoogleSigninTests(unittest.TestCase):
    ha: LiveHA
    family: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.ha = LiveHA("dev", PORT)
        cls.family = cls.ha.tmp / "family.yaml"
        try:
            cls.ha._prepare()
            write_family(cls.family)
            cls.entries_text = synthetic_core_config_entries()
            # (a) the entry goes in the way a reset puts it back: saved, then restored before the first start
            saved = cls.ha.seed("google-save", "--stdin", "--family", str(cls.family), input_text=cls.entries_text)
            if saved.returncode != 0:
                raise RuntimeError("google-save failed: %s %s" % (saved.stdout, saved.stderr))
            restored = cls.ha.seed("google-restore", "--config-dir", str(cls.ha.config_dir), "--family", str(cls.family))
            if restored.returncode != 0:
                raise RuntimeError("google-restore failed: %s %s" % (restored.stdout, restored.stderr))
            cls.ha.start()
        except BaseException:
            cls.ha.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ha.__exit__(None, None, None)

    # -- helpers ------------------------------------------------------------------------------------

    def google_entry(self) -> dict:
        async def read() -> dict:
            async with self.ha.admin_session() as (client, token, _ws):
                status, body = await client.rest("GET", "/api/config/config_entries/entry?domain=google", token=token)
                self.assertEqual(status, 200, body)
                self.assertEqual(len(body), 1, body)
                return body[0]

        return self.ha.run_async(read())

    def credentials(self) -> list[dict]:
        async def read() -> list[dict]:
            async with self.ha.admin_session() as (_client, _token, ws):
                return (await ws.call("application_credentials/list"))["result"]

        return self.ha.run_async(read())

    def link(self) -> subprocess.CompletedProcess:
        return self.ha.seed("google-link", "--family", str(self.family), timeout=300)

    def saved_path(self) -> Path:
        return self.ha.secrets_dir / "google-dev.json"

    # -- the proof ----------------------------------------------------------------------------------

    def test_a_the_restored_entry_is_in_the_instance_before_anything_else(self) -> None:
        self.assertTrue(self.saved_path().is_file())
        bootstrap = self.ha.seed("bootstrap")
        self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
        entry = self.google_entry()
        self.assertEqual(entry["entry_id"], ENTRY_ID)
        self.assertEqual(entry["title"], UNIQUE_ID)

    def test_b_without_the_credential_the_entry_cannot_load(self) -> None:
        entry = self.google_entry()
        print("\nstate before the credential: %s (reason: %s)" % (entry["state"], entry.get("reason")))
        self.assertIn(entry["state"], ("setup_error", "setup_retry"))
        self.assertEqual(self.credentials(), [])

    def test_c_link_creates_the_credential_and_the_entry_loads(self) -> None:
        result = self.link()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("application credential created", result.stdout)
        self.assertIn("loaded", result.stdout)
        entry = self.google_entry()
        print("\nstate after the credential: %s" % entry["state"])
        self.assertEqual(entry["state"], "loaded")
        self.assertEqual([c["client_id"] for c in self.credentials()], [CLIENT_ID])
        again = self.link()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertIn("application credential present", again.stdout)
        self.assertEqual(len(self.credentials()), 1, "the credential is created only once")

    def test_d_saving_the_stopped_instance_keeps_the_same_entry_privately(self) -> None:
        self.ha.stop()
        os.unlink(self.saved_path())
        saved = self.ha.seed("google-save", "--config-dir", str(self.ha.config_dir), "--family", str(self.family))
        self.assertEqual(saved.returncode, 0, saved.stdout + saved.stderr)
        path = self.saved_path()
        self.assertEqual(path, self.ha.secrets_dir / "google-dev.json")
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.ha.secrets_dir.stat().st_mode), 0o700)
        entry = json.loads(path.read_text(encoding="utf-8"))["entry"]
        self.assertEqual(entry["entry_id"], ENTRY_ID)
        self.assertEqual(entry["unique_id"], UNIQUE_ID)
        self.assertEqual(entry["data"]["token"]["refresh_token"], REFRESH_TOKEN)
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout
        self.assertNotIn("google-", status, "a secrets file must never show up inside the repository")
        self.assertNotIn(".ha-secrets", status)

    def test_e_after_a_wipe_the_restored_entry_loads_again(self) -> None:
        self.ha.stop()
        wiped = self.ha.wipe_config()
        self.assertEqual(wiped.returncode, 0, wiped.stdout + wiped.stderr)
        self.assertFalse((self.ha.config_dir / ".storage").exists())
        restored = self.ha.seed("google-restore", "--config-dir", str(self.ha.config_dir), "--family", str(self.family))
        self.assertEqual(restored.returncode, 0, restored.stdout + restored.stderr)
        entries_file = self.ha.config_dir / ".storage" / "core.config_entries"
        self.assertEqual(stat.S_IMODE(entries_file.stat().st_mode), 0o600)
        document = json.loads(entries_file.read_text(encoding="utf-8"))
        self.assertEqual([e["domain"] for e in document["data"]["entries"]], ["google"], "the only entry")
        self.ha.rerender_config()
        self.ha.start()
        bootstrap = self.ha.seed("bootstrap")
        self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
        before = self.google_entry()
        print("\nstate after the wipe, before the credential: %s" % before["state"])
        self.assertIn(before["state"], ("setup_error", "setup_retry"))
        self.assertEqual(self.credentials(), [], "the wipe took the application credential with it")
        result = self.link()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("application credential created", result.stdout)
        entry = self.google_entry()
        print("state after the wipe and the credential: %s" % entry["state"])
        self.assertEqual(entry["state"], "loaded")
        self.assertEqual(entry["entry_id"], ENTRY_ID)

    def test_f_restoring_into_a_directory_that_has_entries_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp) / ".storage"
            storage.mkdir()
            (storage / "core.config_entries").write_text("{}", encoding="utf-8")
            result = self.ha.seed("google-restore", "--config-dir", tmp, "--family", str(self.family))
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual((storage / "core.config_entries").read_text(encoding="utf-8"), "{}", "left untouched")

    def test_g_restore_to_stdout_prints_only_the_file_and_skips_without_a_google_block(self) -> None:
        printed = self.ha.seed("google-restore", "--stdout", "--family", str(self.family))
        self.assertEqual(printed.returncode, 0, printed.stderr)
        document = json.loads(printed.stdout)
        self.assertEqual(document["key"], "core.config_entries")
        self.assertEqual([e["entry_id"] for e in document["data"]["entries"]], [ENTRY_ID])
        plain = self.ha.tmp / "plain.yaml"
        plain.write_text(yaml.safe_dump(yaml.safe_load(family_file.EXAMPLE_FILE.read_text(encoding="utf-8"))), encoding="utf-8")
        skipped = self.ha.seed("google-restore", "--stdout", "--family", str(plain))
        self.assertEqual(skipped.returncode, 0, skipped.stderr)
        self.assertEqual(skipped.stdout, "", "no google block: nothing is restored")
        linked = self.ha.seed("google-link", "--family", str(plain))
        self.assertEqual(linked.returncode, 0, linked.stderr)
        self.assertIn("google: not configured", linked.stdout)


class LiveGoogleNoEntryTests(unittest.TestCase):
    """A fresh instance that was never signed in: the seed says what to do, and the credential is ready."""

    ha: LiveHA
    family: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.ha = LiveHA("dev", PORT)
        cls.ha.__enter__()
        try:
            cls.family = cls.ha.tmp / "family.yaml"
            write_family(cls.family)
            boot = cls.ha.seed("bootstrap")
            if boot.returncode != 0:
                raise RuntimeError("bootstrap failed: %s" % boot.stderr)
        except BaseException:
            cls.ha.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ha.__exit__(None, None, None)

    def test_without_an_entry_link_stops_with_the_one_time_instruction(self) -> None:
        result = self.ha.seed("google-link", "--family", str(self.family), timeout=300)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(SIGNIN_TEXT, result.stderr)
        self.assertIn("dev/GOOGLE.md", result.stderr)
        self.assertIn("First sign-in", result.stderr)

        async def read() -> list[dict]:
            async with self.ha.admin_session() as (_client, _token, ws):
                return (await ws.call("application_credentials/list"))["result"]

        credentials = self.ha.run_async(read())
        self.assertEqual([c["client_id"] for c in credentials], [CLIENT_ID], "ready for the first sign-in")


if __name__ == "__main__":
    unittest.main()
