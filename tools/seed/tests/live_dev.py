"""Live tests: the seed tool against a real Home Assistant (one boot for the whole class).

Run: FH_HASS=$HOME/.cache/fh-hassfest/venv/bin/hass python -B -m unittest discover \
        -s tools/seed/tests -t . -p 'live_dev.py' -v
"""
from __future__ import annotations

import asyncio
import os
import shutil
import stat
import subprocess
import time
import unittest
from collections import Counter

from tools.seed.resources import content_hash

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
        # every command that writes to an existing instance goes through the same guard
        sync = self.ha.seed("resources-sync", "--dry-run", target="preview")
        self.assertEqual(sync.returncode, 3, sync.stderr)

        async def name():
            async with self.ha.admin_ws() as ws:
                return (await ws.call("get_config"))["result"]["location_name"]

        self.assertEqual(self.ha.run_async(name()), "Family Hub DEV")

    def test_f_credentials_are_private(self) -> None:
        path = self.ha.secrets_dir / "credentials-dev.json"
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(self.ha.secrets_dir).st_mode), 0o700)

    def test_g_resources_sync_follows_an_edited_card_and_is_idempotent(self) -> None:
        integration = self.ha.config_dir / "custom_components" / "family_hub"
        card = integration / "card" / "family-today-card.js"
        # Minimal Family Hub entry: every step answered with its smallest valid input.
        answers = {
            "features": {"setup_features": []},
            "calendars": {"calendars": []},
            "notifications": {"default_notify_target": "notify.persistent_notification"},
            "dashboard": {"add_dashboard": False},
            "finish": {},
        }

        async def setup_entry_and_wait_for_resources():
            async with self.ha.admin_session() as (client, token, ws):
                await client.drive_config_flow(token, "family_hub", answers)
                for _ in range(60):
                    rows = (await ws.call("lovelace/resources"))["result"]
                    if any(row["url"].startswith("/family_hub_today_card/") for row in rows):
                        return rows
                    await asyncio.sleep(1)
            raise AssertionError("the integration never registered its card resources")

        rows = self.ha.run_async(setup_entry_and_wait_for_resources())
        self.assertGreaterEqual(len(rows), 13)

        with open(card, "a", encoding="utf-8") as handle:
            handle.write("\n// edited by the live resources-sync test\n")
        new_hash = content_hash(str(card))

        args = ("resources-sync", "--integration-dir", str(integration))
        first = self.ha.seed(*args)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("resources: 1 updated", first.stdout)
        second = self.ha.seed(*args)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("resources: 0 updated", second.stdout)

        async def read_rows():
            async with self.ha.admin_ws() as ws:
                return (await ws.call("lovelace/resources"))["result"]

        rows = self.ha.run_async(read_rows())
        today = [row for row in rows if row["url"].startswith("/family_hub_today_card/")]
        self.assertEqual(len(today), 1)
        self.assertTrue(today[0]["url"].endswith("?v=" + new_hash), today[0]["url"])
        per_path = Counter(row["url"].split("?", 1)[0] for row in rows)
        self.assertEqual(max(per_path.values()), 1, per_path)


if __name__ == "__main__":
    unittest.main()
