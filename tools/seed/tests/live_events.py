"""Live D-11 proof: tagged events are planned, created, kept and cleaned on a real Local Calendar.

One Home Assistant boot (port 18132, target dev). Two Local Calendars ("Sam", "Jordan") hold
seven pre-existing events: real-looking untagged ones, the other environment's, look-alikes that
carry only half of the tag-and-marker pair, one stale genuine [DEV] event and one genuine [DEV]
event outside the bounded window. Only the stale in-window one may ever be deleted.

Run: FH_HASS=$HOME/.cache/fh-hassfest/venv/bin/hass python -B -m unittest discover \
        -s tools/seed/tests -t . -p 'live_events.py' -v
"""
from __future__ import annotations

import datetime
import os
import re
import subprocess
import sys
import unittest
from urllib.parse import quote

from tools.seed import events as events_mod
from tools.seed.envs import ENVIRONMENTS

from .live_ha import HOST_ENV, REPO_ROOT, LiveHA

SAM = "calendar.sam"
JORDAN = "calendar.jordan"
CALENDARS = ["--calendar", "%s=Sam" % SAM, "--calendar", "%s=Jordan" % JORDAN]
DEV = ENVIRONMENTS["dev"]
SLOTS = [events_mod.CalendarSlot("Sam", SAM), events_mod.CalendarSlot("Jordan", JORDAN)]

REAL_TODAY = datetime.date.today()
MONDAY = REAL_TODAY - datetime.timedelta(days=REAL_TODAY.weekday())
WEDNESDAY = MONDAY + datetime.timedelta(days=2)  # fixed weekday so every run plans the same shape


def dev_marker(key: str) -> str:
    return "family-hub-seed:dev:" + key


def at(day: datetime.date, hour: int = 10) -> datetime.datetime:
    return datetime.datetime.combine(day, datetime.time(hour))


# (name, entity, summary, description, start); u1..u7 as described in the plan, plus u7 (outside window).
PRESET = [
    ("u1", SAM, "Dentist", None, at(MONDAY + datetime.timedelta(days=3))),
    ("u2", JORDAN, "[PREVIEW] School run", "family-hub-seed:preview:2026w01-1-1-jordan", at(MONDAY + datetime.timedelta(days=1))),
    ("u3", SAM, "[DEV] Old event", dev_marker("old-event"), at(MONDAY - datetime.timedelta(days=21))),
    ("u4", SAM, "[DEV] No marker", None, at(MONDAY + datetime.timedelta(days=4))),
    ("u5", JORDAN, "Meeting [DEV] notes", dev_marker("meeting-notes"), at(MONDAY + datetime.timedelta(days=3), 14)),
    ("u6", SAM, "Piano", dev_marker("piano"), at(MONDAY + datetime.timedelta(days=5), 15)),
    ("u7", JORDAN, "[DEV] Ancient event", dev_marker("ancient"), at(MONDAY - datetime.timedelta(days=60))),
]
SURVIVORS = ("u1", "u2", "u4", "u5", "u6", "u7")


class LiveEventsTests(unittest.TestCase):
    ha: LiveHA
    uids: dict[str, str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.ha = LiveHA("dev", 18132)
        cls.ha.__enter__()
        try:
            boot = cls.ha.seed("bootstrap")
            if boot.returncode != 0:
                raise RuntimeError("bootstrap failed: %s" % boot.stderr)
            cls.ha.run_async(cls._create_world())
            cls.uids = {}
            for name, entity, summary, _description, _start in PRESET:
                cls.uids[name] = cls._uid_of(entity, summary)
        except BaseException:
            cls.ha.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ha.__exit__(None, None, None)

    # -- fixtures -----------------------------------------------------------------------------------

    @classmethod
    async def _create_world(cls) -> None:
        async with cls.ha.admin_session() as (client, token, _ws):
            for name in ("Sam", "Jordan"):
                await client.drive_config_flow(
                    token, "local_calendar", {"user": {"calendar_name": name, "import": "create_empty"}}
                )
            for _name, entity, summary, description, start in PRESET:
                payload = {
                    "entity_id": entity,
                    "summary": summary,
                    "start_date_time": start.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_date_time": (start + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
                }
                if description:
                    payload["description"] = description
                status, body = await client.rest("POST", "/api/services/calendar/create_event", json=payload, token=token)
                assert status == 200, (status, body)

    @classmethod
    def _uid_of(cls, entity: str, summary: str) -> str:
        found = [e for e in cls.events_of(entity) if e["summary"] == summary]
        assert len(found) == 1, (entity, summary, found)
        return found[0]["uid"]

    @classmethod
    def events_of(cls, entity: str) -> list[dict]:
        async def read():
            async with cls.ha.admin_session() as (client, token, _ws):
                start = (MONDAY - datetime.timedelta(days=90)).isoformat() + "T00:00:00"
                end = (MONDAY + datetime.timedelta(days=60)).isoformat() + "T00:00:00"
                path = "/api/calendars/%s?start=%s&end=%s" % (entity, quote(start), quote(end))
                status, body = await client.rest("GET", path, token=token)
                assert status == 200, (status, body)
                return body

        return cls.ha.run_async(read())

    def all_events(self) -> dict[str, dict]:
        """uid -> event over both calendars (uids are unique per event)."""
        merged: dict[str, dict] = {}
        for entity in (SAM, JORDAN):
            for event in self.events_of(entity):
                merged[event["uid"]] = dict(event, entity_id=entity)
        return merged

    def tagged(self) -> list[dict]:
        return [e for e in self.all_events().values() if e["summary"].startswith(DEV.tag)
                and "family-hub-seed:dev:" in (e.get("description") or "")
                and e["uid"] not in self.uids.values()]

    def run_events(self, command: str, *extra: str) -> subprocess.CompletedProcess:
        argv = [
            sys.executable, "-B", "-m", "tools.seed.events",
            "--target", "dev",
            "--base-url", self.ha.base_url,
            "--ca", self.ha.ca,
            "--secrets-dir", str(self.ha.secrets_dir),
            command, *CALENDARS, "--today", WEDNESDAY.isoformat(), *extra,
        ]
        return subprocess.run(
            argv, cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **HOST_ENV),
        )

    def assert_survivors_intact(self) -> None:
        present = self.all_events()
        for name in SURVIVORS:
            self.assertIn(self.uids[name], present, "%s was deleted" % name)

    def counts(self, text: str) -> tuple[int, int, int]:
        found = re.search(r"events: create (\d+), delete (\d+), keep (\d+)", text)
        self.assertIsNotNone(found, text)
        return int(found.group(1)), int(found.group(2)), int(found.group(3))

    # -- the proof ----------------------------------------------------------------------------------

    def test_a_fixture_has_all_seven_events_and_nothing_tagged_by_the_seed(self) -> None:
        self.assertEqual(sorted(self.uids), ["u1", "u2", "u3", "u4", "u5", "u6", "u7"])
        self.assertEqual(len(set(self.uids.values())), 7)
        self.assertEqual(self.tagged(), [])

    def test_b_dry_run_writes_nothing(self) -> None:
        before = self.all_events()
        result = self.run_events("sync")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("(dry run)", result.stdout)
        create, delete, _keep = self.counts(result.stdout)
        self.assertGreater(create, 0)
        self.assertEqual(delete, 1)
        self.assertIn("DELETE %s" % SAM, result.stdout)
        self.assertIn("[DEV] Old event", result.stdout)
        self.assertEqual(self.all_events().keys(), before.keys())

    def test_c_apply_deletes_only_the_stale_event_and_creates_the_plan(self) -> None:
        planned = events_mod.plan_week_events(SLOTS, DEV, WEDNESDAY)
        result = self.run_events("sync", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("(applied)", result.stdout)
        self.assertEqual(self.counts(result.stdout), (len(planned), 1, 0))
        present = self.all_events()
        self.assertNotIn(self.uids["u3"], present, "the stale in-window [DEV] event should be gone")
        self.assert_survivors_intact()
        created = [e for e in present.values() if e["uid"] not in self.uids.values()]
        self.assertEqual(len(created), len(planned))
        self.assertEqual(
            sorted((e["entity_id"], e["summary"]) for e in created),
            sorted((p.entity_id, p.summary) for p in planned),
        )
        for event in created:
            self.assertTrue(event["description"].startswith("family-hub-seed:dev:"), event)

    def test_d_second_apply_changes_nothing(self) -> None:
        before = self.all_events()
        result = self.run_events("sync", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("create 0, delete 0", result.stdout)
        self.assertEqual(self.all_events().keys(), before.keys(), "no event was re-created")
        self.assert_survivors_intact()

    def test_e_clean_dry_run_then_apply_removes_only_the_created_events(self) -> None:
        planned = events_mod.plan_week_events(SLOTS, DEV, WEDNESDAY)
        dry = self.run_events("clean")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("(dry run)", dry.stdout)
        self.assertEqual(self.counts(dry.stdout), (0, len(planned), 0))
        self.assertEqual(len(self.all_events()), len(planned) + len(SURVIVORS))
        applied = self.run_events("clean", "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(self.counts(applied.stdout), (0, len(planned), 0))
        self.assertEqual(sorted(self.all_events()), sorted(self.uids[name] for name in SURVIVORS))
        self.assert_survivors_intact()

    def test_f_a_read_only_calendar_is_never_written(self) -> None:
        argv_extra = ["--apply"]
        command = [
            sys.executable, "-B", "-m", "tools.seed.events", "--target", "dev",
            "--base-url", self.ha.base_url, "--ca", self.ha.ca, "--secrets-dir", str(self.ha.secrets_dir),
            "sync", "--calendar", "%s=Sam" % SAM, "--calendar", "%s=Jordan:ro" % JORDAN,
            "--today", WEDNESDAY.isoformat(), *argv_extra,
        ]
        result = subprocess.run(
            command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **HOST_ENV),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        jordan = {e["uid"] for e in self.events_of(JORDAN)}
        self.assertEqual(jordan, {self.uids["u2"], self.uids["u5"], self.uids["u7"]}, "Jordan is read-only")
        cleanup = self.run_events("clean", "--apply")
        self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
        self.assert_survivors_intact()


if __name__ == "__main__":
    unittest.main()
