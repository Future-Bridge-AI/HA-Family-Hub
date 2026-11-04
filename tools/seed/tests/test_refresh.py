"""Unit tests for what the refresh and the event sync wiring need from the seed tool's own modules.

The live behaviour (events appear, a second refresh changes nothing, a registered phone is removed
from the notify targets) is in live_preview.py; the script wiring is in test_scripts.py.

Run: python -B -m unittest discover -s tools/seed/tests -t . -p 'test_*.py' -v
"""
from __future__ import annotations

import dataclasses
import re
import unittest
from pathlib import Path

from tools.seed import __main__ as seed_main
from tools.seed import entries, events, family_file

MAIN_SOURCE = Path(seed_main.__file__).read_text(encoding="utf-8")
CALENDARS = {
    "Sam": "calendar.sam",
    "Jordan": "calendar.jordan",
    "Riley": "calendar.riley",
    "Casey": "calendar.casey",
}


class CalendarSlotsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.family = family_file.load(None, lambda _line: None)

    def test_every_local_calendar_becomes_a_writable_slot_in_family_order(self) -> None:
        slots = entries.calendar_slots(self.family, CALENDARS)
        self.assertEqual(
            slots,
            [events.CalendarSlot(person=name, entity_id=entity, writable=True) for name, entity in CALENDARS.items()],
        )
        self.assertEqual([slot.person for slot in slots], [m.first_name for m in self.family.members])

    def test_a_member_without_a_local_calendar_gets_no_slot(self) -> None:
        members = tuple(
            dataclasses.replace(m, calendar="google") if m.first_name == "Jordan" else m for m in self.family.members
        )
        slots = entries.calendar_slots(dataclasses.replace(self.family, members=members), CALENDARS)
        self.assertEqual([slot.person for slot in slots], ["Sam", "Riley", "Casey"])

    def test_a_calendar_that_was_not_created_is_skipped_rather_than_guessed(self) -> None:
        partial = {name: entity for name, entity in CALENDARS.items() if name != "Casey"}
        slots = entries.calendar_slots(self.family, partial)
        self.assertEqual([slot.person for slot in slots], ["Sam", "Jordan", "Riley"])

    def test_no_calendars_means_no_slots(self) -> None:
        self.assertEqual(entries.calendar_slots(self.family, {}), [])


class WiringTests(unittest.TestCase):
    def test_seed_and_refresh_both_run_the_event_sync_with_apply(self) -> None:
        calls = re.findall(r"events\.sync\(([^)]*)\)", MAIN_SOURCE)
        self.assertGreaterEqual(len(calls), 2, calls)
        for call in calls:
            self.assertIn("apply=True", call)

    def test_refresh_is_a_command_with_the_family_and_integration_options(self) -> None:
        self.assertIn("refresh", seed_main.COMMANDS)
        parsed = seed_main.build_parser().parse_args(
            ["--target", "preview", "refresh", "--family", "x.yaml", "--integration-dir", "somewhere"]
        )
        self.assertEqual((parsed.command, parsed.family, parsed.integration_dir), ("refresh", "x.yaml", "somewhere"))

    def test_refresh_never_deletes_family_hub_data_or_resets_anything(self) -> None:
        start = MAIN_SOURCE.index("async def _cmd_refresh")
        body = MAIN_SOURCE[start : MAIN_SOURCE.index("COMMANDS: dict", start)]
        for forbidden in ("bootstrap_mod.bootstrap(", "delete", "wipe", "reset", "clean("):
            self.assertNotIn(forbidden, body)
        for needed in (
            "remove_outbound_entries",
            "apply_content",
            "events.sync(",
            "apply_safe_notifications",
            "_verify(",
        ):
            self.assertIn(needed, body)

    def test_the_refresh_order_ends_with_safe_notifications_then_verify(self) -> None:
        start = MAIN_SOURCE.index("async def _cmd_refresh")
        body = MAIN_SOURCE[start : MAIN_SOURCE.index("COMMANDS: dict", start)]
        order = [body.find(word) for word in ("apply_content", "events.sync(", "apply_safe_notifications", "_verify(")]
        self.assertNotIn(-1, order, "every step must be in the refresh")
        self.assertEqual(order, sorted(order))


if __name__ == "__main__":
    unittest.main()
