"""Google calendar selection and slots (D-07, D-11, D-25) and the pure parts of the sign-in keeping (D-10).

No Home Assistant is needed: the entity registry is a list of dicts, the websocket and the REST client are
small fakes. The live proof of the sign-in mechanics is live_google.py.
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
import stat
import tempfile
import unittest

import yaml

from tools.seed import events, family_file
from tools.seed import google as google_mod
from tools.seed.client import SeedError
from tools.seed.envs import ENVIRONMENTS

FAMILY_CAL = "family123@group.calendar.google.com"
SCHOOL_CAL = "school456@group.calendar.google.com"
ACCOUNT = "owner@example.com"
ICAL = "https://calendar.google.com/calendar/ical/family123%40group.calendar.google.com/private-0123abcd/basic.ics"


def family_with_google():
    data = yaml.safe_load(family_file.EXAMPLE_FILE.read_text(encoding="utf-8"))
    data["members"][1]["calendar"] = "google:family"
    data["google"] = {
        "client_id": "test-client.apps.googleusercontent.com",
        "client_secret": "test-secret",
        "calendars": [
            {
                "key": "family",
                "calendar_id": FAMILY_CAL,
                "person": "Jordan",
                "writable": True,
                "expect_events": True,
                "backup": "ical",
                "ical_secret_url": ICAL,
            },
            {
                "key": "school",
                "calendar_id": SCHOOL_CAL,
                "person": "Riley",
                "writable": False,
                "expect_events": False,
                "backup": "ha-snapshot",
            },
        ],
    }
    return family_file.parse(copy.deepcopy(data)), data


def entity(entity_id: str, unique_id: str, platform: str = "google", disabled_by=None, entry: str = "E1") -> dict:
    return {
        "entity_id": entity_id,
        "unique_id": unique_id,
        "platform": platform,
        "disabled_by": disabled_by,
        "config_entry_id": entry,
    }


class SelectEntitiesTests(unittest.TestCase):
    def registry(self) -> list[dict]:
        return [
            entity("calendar.family", "%s-%s" % (ACCOUNT, FAMILY_CAL)),
            entity("calendar.school", "%s-%s" % (ACCOUNT, SCHOOL_CAL), disabled_by="user"),
            entity("calendar.owner", "%s-%s" % (ACCOUNT, ACCOUNT)),
            entity("calendar.birthdays", "%s-%s-birthdays" % (ACCOUNT, ACCOUNT)),
            entity("calendar.work_location", "%s-%s-work-location" % (ACCOUNT, ACCOUNT), disabled_by="integration"),
            entity("calendar.holidays", "%s-holidays@group.v.calendar.google.com" % ACCOUNT),
            entity("calendar.lookalike", "other-prefix-%s" % FAMILY_CAL),
            entity("calendar.local_family", "%s-%s" % (ACCOUNT, FAMILY_CAL), platform="local_calendar"),
            entity("sensor.something", "%s-%s" % (ACCOUNT, FAMILY_CAL), platform="template"),
        ]

    def test_keeps_exactly_the_chosen_calendars_by_their_full_unique_id(self) -> None:
        picked = google_mod.select_entities(self.registry(), ACCOUNT, [FAMILY_CAL, SCHOOL_CAL])
        self.assertEqual(sorted(picked.keep), ["calendar.family", "calendar.school"])

    def test_every_other_google_entity_is_disabled_birthdays_and_work_location_included(self) -> None:
        picked = google_mod.select_entities(self.registry(), ACCOUNT, [FAMILY_CAL])
        self.assertIn("calendar.owner", picked.disable)
        self.assertIn("calendar.birthdays", picked.disable)
        self.assertIn("calendar.holidays", picked.disable)
        self.assertIn("calendar.school", picked.keep + picked.disable + picked.enable)
        self.assertNotIn("calendar.family", picked.disable)

    def test_a_lookalike_that_only_ends_with_a_chosen_id_is_disabled(self) -> None:
        picked = google_mod.select_entities(self.registry(), ACCOUNT, [FAMILY_CAL])
        self.assertIn("calendar.lookalike", picked.disable)
        self.assertNotIn("calendar.lookalike", picked.keep)

    def test_a_chosen_entity_the_developer_disabled_is_enabled_again(self) -> None:
        picked = google_mod.select_entities(self.registry(), ACCOUNT, [SCHOOL_CAL])
        self.assertEqual(picked.enable, ["calendar.school"])
        self.assertEqual(picked.keep, ["calendar.school"])
        self.assertNotIn("calendar.school", picked.disable)

    def test_entities_that_are_already_disabled_are_left_alone(self) -> None:
        picked = google_mod.select_entities(self.registry(), ACCOUNT, [FAMILY_CAL])
        self.assertNotIn("calendar.school", picked.disable)
        self.assertNotIn("calendar.work_location", picked.disable)

    def test_other_platforms_are_never_touched(self) -> None:
        picked = google_mod.select_entities(self.registry(), ACCOUNT, [FAMILY_CAL])
        everything = picked.keep + picked.disable + picked.enable
        self.assertNotIn("calendar.local_family", everything)
        self.assertNotIn("sensor.something", everything)

    def test_missing_chosen_calendars_are_reported(self) -> None:
        picked = google_mod.select_entities(self.registry(), ACCOUNT, [FAMILY_CAL, "nowhere@example.com"])
        self.assertEqual(picked.missing, ["nowhere@example.com"])

    def test_an_entry_id_limits_the_selection_to_that_entry(self) -> None:
        registry = self.registry() + [entity("calendar.other_entry", "x-%s" % FAMILY_CAL, entry="E2")]
        picked = google_mod.select_entities(registry, ACCOUNT, [FAMILY_CAL], entry_id="E1")
        self.assertNotIn("calendar.other_entry", picked.disable)


class GoogleSlotsTests(unittest.TestCase):
    def test_only_writable_and_expect_events_calendars_get_writable_slots(self) -> None:
        family, _data = family_with_google()
        slots = google_mod.google_slots(family, {"family": "calendar.family", "school": "calendar.school"})
        self.assertEqual(
            slots,
            [
                events.CalendarSlot(person="Jordan", entity_id="calendar.family", writable=True),
                events.CalendarSlot(person="Riley", entity_id="calendar.school", writable=False),
            ],
        )

    def test_writable_without_expect_events_is_not_written_to(self) -> None:
        family, data = family_with_google()
        data["google"]["calendars"][0]["expect_events"] = False
        family = family_file.parse(data)
        slots = google_mod.google_slots(family, {"family": "calendar.family", "school": "calendar.school"})
        self.assertFalse(any(slot.writable for slot in slots))

    def test_a_calendar_without_an_entity_gets_no_slot(self) -> None:
        family, _data = family_with_google()
        slots = google_mod.google_slots(family, {"family": "calendar.family"})
        self.assertEqual([slot.entity_id for slot in slots], ["calendar.family"])

    def test_no_google_block_no_slots(self) -> None:
        family = family_file.load(str(family_file.EXAMPLE_FILE), lambda _line: None)
        self.assertEqual(google_mod.google_slots(family, {}), [])

    def test_a_member_with_a_google_calendar_maps_to_that_entity(self) -> None:
        family, _data = family_with_google()
        mapped = google_mod.member_calendars(family, {"family": "calendar.family", "school": "calendar.school"})
        self.assertEqual(mapped, {"Jordan": "calendar.family"})

    def test_the_event_sync_allow_list_holds_only_writable_google_and_local_slots(self) -> None:
        from tools.seed import entries as entries_mod

        family, _data = family_with_google()
        local = {"Sam": "calendar.sam", "Riley": "calendar.riley", "Casey": "calendar.casey"}
        google_slots = google_mod.google_slots(family, {"family": "calendar.family", "school": "calendar.school"})
        slots = entries_mod.calendar_slots(family, local, google_slots)
        writable = {slot.entity_id for slot in slots if slot.writable}
        self.assertEqual(writable, {"calendar.sam", "calendar.riley", "calendar.casey", "calendar.family"})
        self.assertNotIn("calendar.school", writable)


class SavedEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.secrets = os.path.join(self._tmp.name, "secrets")

    def entries_file(self, *domains: str) -> str:
        entries = [{"domain": d, "entry_id": "id-%s" % d, "unique_id": d, "data": {"token": {"refresh_token": "r-%s" % d}}} for d in domains]
        return json.dumps({"version": 1, "minor_version": 5, "key": "core.config_entries", "data": {"entries": entries}})

    def test_saves_the_one_google_entry_privately(self) -> None:
        said: list[str] = []
        wrote = google_mod.save_entry(self.entries_file("local_todo", "google"), self.secrets, "dev", said.append)
        self.assertTrue(wrote)
        path = os.path.join(self.secrets, "google-dev.json")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
        saved = json.load(open(path, encoding="utf-8"))
        self.assertEqual((saved["version"], saved["minor_version"]), (1, 5))
        self.assertEqual(saved["entry"]["entry_id"], "id-google")

    def test_with_no_google_entry_nothing_changes(self) -> None:
        said: list[str] = []
        self.assertFalse(google_mod.save_entry(self.entries_file("local_todo"), self.secrets, "dev", said.append))
        self.assertEqual(said, ["google: no entry to save"])
        self.assertFalse(os.path.exists(os.path.join(self.secrets, "google-dev.json")))

    def test_an_older_save_survives_a_run_with_no_entry(self) -> None:
        google_mod.save_entry(self.entries_file("google"), self.secrets, "dev", lambda _l: None)
        google_mod.save_entry(self.entries_file("local_todo"), self.secrets, "dev", lambda _l: None)
        self.assertTrue(os.path.exists(os.path.join(self.secrets, "google-dev.json")))

    def test_two_google_entries_are_refused(self) -> None:
        with self.assertRaises(SeedError):
            google_mod.save_entry(self.entries_file("google", "google"), self.secrets, "dev", lambda _l: None)

    def test_restore_gives_only_the_google_entry_with_the_saved_versions(self) -> None:
        google_mod.save_entry(self.entries_file("local_todo", "google"), self.secrets, "dev", lambda _l: None)
        text = google_mod.restore_entry(self.secrets, "dev")
        document = json.loads(text)
        self.assertEqual(document["key"], "core.config_entries")
        self.assertEqual((document["version"], document["minor_version"]), (1, 5))
        self.assertEqual([e["domain"] for e in document["data"]["entries"]], ["google"])

    def test_restore_with_nothing_saved_is_none(self) -> None:
        self.assertIsNone(google_mod.restore_entry(self.secrets, "dev"))

    def test_dev_and_preview_are_saved_separately(self) -> None:
        google_mod.save_entry(self.entries_file("google"), self.secrets, ENVIRONMENTS["dev"], lambda _l: None)
        self.assertIsNone(google_mod.restore_entry(self.secrets, ENVIRONMENTS["preview"]))


class FakeWebSocket:
    def __init__(self, credentials: list[dict], flows: list[dict] | None = None) -> None:
        self.credentials = credentials
        self.calls: list[tuple] = []
        self.flows = flows or []

    async def call(self, type: str, **fields):
        self.calls.append((type, fields))
        if type == "application_credentials/list":
            return {"result": list(self.credentials)}
        if type == "application_credentials/create":
            self.credentials.append(dict(fields))
            return {"result": dict(fields)}
        if type == "config_entries/flow/progress":
            return {"result": self.flows}
        raise AssertionError(type)


class FakeClient:
    """REST answers for the google entry: a state per poll, in order."""

    def __init__(self, states: list[str], entry_id: str = "E1", no_entry: bool = False) -> None:
        self.states = list(states)
        self.entry_id = entry_id
        self.no_entry = no_entry
        self.requests: list[tuple[str, str]] = []

    async def rest(self, method: str, path: str, json=None, data=None, token=None):
        self.requests.append((method, path))
        if path.startswith("/api/config/config_entries/entry?domain=google"):
            if self.no_entry:
                return 200, []
            state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
            return 200, [{"entry_id": self.entry_id, "state": state, "reason": "boom" if state != "loaded" else None}]
        if method == "POST" and path.endswith("/reload"):
            return 200, {"require_restart": False}
        return 200, {}


BLOCK = {"client_id": "test-client.apps.googleusercontent.com", "client_secret": "s3cret", "calendars": []}


class CredentialAndLinkTests(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    def test_creates_the_credential_only_when_none_matches_the_client_id(self) -> None:
        ws = FakeWebSocket([])
        self.assertEqual(self.run_async(google_mod.ensure_credential(ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None)), "created")
        create = [fields for kind, fields in ws.calls if kind == "application_credentials/create"][0]
        self.assertEqual(create["domain"], "google")
        self.assertEqual(create["name"], "Family Hub dev")
        self.assertEqual(self.run_async(google_mod.ensure_credential(ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None)), "present")
        self.assertEqual(len([c for c in ws.calls if c[0] == "application_credentials/create"]), 1)

    def test_a_credential_of_another_client_does_not_count(self) -> None:
        ws = FakeWebSocket([{"domain": "google", "client_id": "someone-else"}])
        self.assertEqual(self.run_async(google_mod.ensure_credential(ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None)), "created")

    def test_link_reloads_and_returns_when_loaded(self) -> None:
        client, ws = FakeClient(["loaded"]), FakeWebSocket([])
        entry = self.run_async(google_mod.link(client, "t", ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None, timeout=5))
        self.assertEqual(entry["state"], "loaded")
        self.assertIn(("POST", "/api/config/config_entries/entry/E1/reload"), client.requests)

    def test_link_without_reload_only_checks(self) -> None:
        client, ws = FakeClient(["loaded"]), FakeWebSocket([])
        self.run_async(google_mod.link(client, "t", ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None, timeout=5, reload=False))
        self.assertFalse([r for r in client.requests if r[0] == "POST"])

    def test_setup_error_prints_the_one_time_sign_in_instruction(self) -> None:
        client, ws = FakeClient(["setup_error"]), FakeWebSocket([])
        with self.assertRaises(SeedError) as caught:
            self.run_async(google_mod.link(client, "t", ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None, timeout=5))
        self.assertEqual(caught.exception.code, "google_signin")
        self.assertIn("dev/GOOGLE.md, First sign-in", caught.exception.message)
        self.assertIn("setup_error", caught.exception.message)

    def test_setup_retry_with_a_reauth_flow_pending_is_the_same_instruction(self) -> None:
        flows = [{"context": {"source": "reauth", "entry_id": "E1"}}]
        client, ws = FakeClient(["setup_retry"]), FakeWebSocket([], flows)
        with self.assertRaises(SeedError) as caught:
            self.run_async(google_mod.link(client, "t", ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None, timeout=5))
        self.assertEqual(caught.exception.code, "google_signin")
        self.assertIn("setup_retry", caught.exception.message)

    def test_no_entry_at_all_is_the_same_instruction_and_the_credential_is_still_created(self) -> None:
        client, ws = FakeClient([], no_entry=True), FakeWebSocket([])
        with self.assertRaises(SeedError) as caught:
            self.run_async(google_mod.link(client, "t", ws, BLOCK, ENVIRONMENTS["dev"], say=lambda _l: None, timeout=5))
        self.assertEqual(caught.exception.code, "google_signin")
        self.assertEqual(len(ws.credentials), 1)


if __name__ == "__main__":
    unittest.main()
