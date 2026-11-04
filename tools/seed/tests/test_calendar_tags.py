"""The D-11 matcher: every look-alike and every boundary. All cases are for env dev unless noted.

calendar_tags.matches() is the only gate before a delete, so each condition is pinned on its own:
a case that flips exactly one thing about an otherwise valid event must be refused.
"""
from __future__ import annotations

import datetime
import unittest

from tools.seed import calendar_tags
from tools.seed.envs import ENVIRONMENTS

DEV = ENVIRONMENTS["dev"]
PREVIEW = ENVIRONMENTS["preview"]
WINDOW_START = datetime.datetime(2026, 11, 2)
WINDOW_END = datetime.datetime(2026, 11, 16)
ALLOWED = {"calendar.sam", "calendar.jordan"}
CAL = "calendar.sam"


def event(**changes):
    """A valid, deletable [DEV] event shaped like HA's GET /api/calendars response."""
    base = {
        "summary": "[DEV] Dentist",
        "description": "family-hub-seed:dev:2026w45-3-1-sam",
        "start": {"dateTime": "2026-11-04T10:00:00+00:00"},
        "end": {"dateTime": "2026-11-04T11:00:00+00:00"},
        "uid": "abc",
        "recurrence_id": None,
        "rrule": None,
    }
    base.update(changes)
    return base


def ok(ev, env=DEV, calendar=CAL, allowed=ALLOWED, start=WINDOW_START, end=WINDOW_END) -> bool:
    return calendar_tags.matches(ev, env, calendar, allowed, start, end)


class MatchesTests(unittest.TestCase):
    def test_exact_tag_and_marker_inside_the_window_matches(self) -> None:
        self.assertTrue(ok(event()))

    def test_untagged_event_is_refused(self) -> None:
        self.assertFalse(ok(event(summary="Dentist")))

    def test_other_environments_tag_is_refused(self) -> None:
        self.assertFalse(ok(event(summary="[PREVIEW] Dentist")))

    def test_tag_in_the_middle_of_the_title_is_refused(self) -> None:
        self.assertFalse(ok(event(summary="Meeting [DEV] notes")))

    def test_tag_without_the_trailing_space_is_refused(self) -> None:
        self.assertFalse(ok(event(summary="[DEV]x")))

    def test_lower_case_tag_is_refused(self) -> None:
        self.assertFalse(ok(event(summary="[dev] Dentist")))

    def test_leading_space_before_the_tag_is_refused(self) -> None:
        self.assertFalse(ok(event(summary=" [DEV] Dentist")))

    def test_missing_marker_is_refused(self) -> None:
        self.assertFalse(ok(event(description=None)))
        self.assertFalse(ok(event(description="")))
        self.assertFalse(ok(event(description="just some notes")))

    def test_marker_for_the_other_environment_is_refused(self) -> None:
        self.assertFalse(ok(event(description="family-hub-seed:preview:2026w45-3-1-sam")))

    def test_marker_with_trailing_text_is_refused(self) -> None:
        self.assertFalse(ok(event(description="family-hub-seed:dev:2026w45-3-1-sam extra")))

    def test_marker_with_leading_text_is_refused(self) -> None:
        self.assertFalse(ok(event(description="note: family-hub-seed:dev:2026w45-3-1-sam")))

    def test_marker_key_with_upper_case_is_refused(self) -> None:
        self.assertFalse(ok(event(description="family-hub-seed:dev:2026W45-3-1-Sam")))

    def test_marker_key_with_underscore_is_refused(self) -> None:
        self.assertFalse(ok(event(description="family-hub-seed:dev:2026w45_3_1_sam")))

    def test_empty_marker_key_is_refused(self) -> None:
        self.assertFalse(ok(event(description="family-hub-seed:dev:")))

    def test_marker_on_its_own_line_among_other_lines_matches(self) -> None:
        self.assertTrue(ok(event(description="Bring the form\nfamily-hub-seed:dev:2026w45-3-1-sam\nthanks")))

    def test_recurring_event_with_rrule_is_refused(self) -> None:
        self.assertFalse(ok(event(rrule="FREQ=WEEKLY")))

    def test_recurring_instance_with_recurrence_id_is_refused(self) -> None:
        self.assertFalse(ok(event(recurrence_id="20261104T100000")))

    def test_start_one_second_before_the_window_is_refused(self) -> None:
        before = WINDOW_START - datetime.timedelta(seconds=1)
        self.assertFalse(ok(event(start={"dateTime": before.isoformat()})))

    def test_start_exactly_at_the_window_start_matches(self) -> None:
        self.assertTrue(ok(event(start={"dateTime": WINDOW_START.isoformat()})))

    def test_start_exactly_at_the_window_end_is_refused(self) -> None:
        self.assertFalse(ok(event(start={"dateTime": WINDOW_END.isoformat()})))

    def test_start_one_second_before_the_window_end_matches(self) -> None:
        last = WINDOW_END - datetime.timedelta(seconds=1)
        self.assertTrue(ok(event(start={"dateTime": last.isoformat()})))

    def test_calendar_not_on_the_allow_list_is_refused(self) -> None:
        self.assertFalse(ok(event(), calendar="calendar.family"))

    def test_empty_allow_list_refuses_everything(self) -> None:
        self.assertFalse(ok(event(), allowed=set()))

    def test_all_day_event_on_the_first_window_date_matches(self) -> None:
        self.assertTrue(ok(event(start={"date": "2026-11-02"}, end={"date": "2026-11-03"})))

    def test_all_day_event_the_day_before_the_window_is_refused(self) -> None:
        self.assertFalse(ok(event(start={"date": "2026-11-01"}, end={"date": "2026-11-02"})))

    def test_all_day_event_on_the_window_end_date_is_refused(self) -> None:
        self.assertFalse(ok(event(start={"date": "2026-11-16"}, end={"date": "2026-11-17"})))

    def test_unreadable_start_is_refused(self) -> None:
        self.assertFalse(ok(event(start=None)))
        self.assertFalse(ok(event(start={"dateTime": "not a date"})))
        self.assertFalse(ok(event(start="garbage")))

    def test_missing_or_non_string_summary_is_refused(self) -> None:
        self.assertFalse(ok(event(summary=None)))
        self.assertFalse(ok(event(summary=123)))

    def test_preview_environment_matches_only_its_own_events(self) -> None:
        preview = event(summary="[PREVIEW] Dentist", description="family-hub-seed:preview:2026w45-3-1-sam")
        self.assertTrue(ok(preview, env=PREVIEW))
        self.assertFalse(ok(preview, env=DEV))
        self.assertFalse(ok(event(), env=PREVIEW))

    def test_allow_list_given_as_one_string_is_a_programming_error(self) -> None:
        with self.assertRaises(TypeError):
            ok(event(), allowed="calendar.sam")


class MarkerTests(unittest.TestCase):
    def test_marker_round_trips(self) -> None:
        line = calendar_tags.marker(DEV, "2026w45-3-1-sam")
        self.assertEqual(line, "family-hub-seed:dev:2026w45-3-1-sam")
        self.assertEqual(calendar_tags.parse_marker(line, DEV), "2026w45-3-1-sam")

    def test_marker_rejects_an_invalid_key(self) -> None:
        for bad in ("", "Sam", "a_b", "a b", "a:b", "ü"):
            with self.assertRaises(ValueError, msg=bad):
                calendar_tags.marker(DEV, bad)

    def test_parse_marker_takes_the_first_valid_line(self) -> None:
        text = "family-hub-seed:dev:Bad_Key\nfamily-hub-seed:dev:first\nfamily-hub-seed:dev:second"
        self.assertEqual(calendar_tags.parse_marker(text, DEV), "first")

    def test_parse_marker_is_none_for_none_and_other_environment(self) -> None:
        self.assertIsNone(calendar_tags.parse_marker(None, DEV))
        self.assertIsNone(calendar_tags.parse_marker("family-hub-seed:preview:abc", DEV))

    def test_parse_marker_does_not_accept_a_trailing_newline_as_part_of_the_key(self) -> None:
        self.assertEqual(calendar_tags.parse_marker("family-hub-seed:dev:abc\n", DEV), "abc")
        self.assertIsNone(calendar_tags.parse_marker("family-hub-seed:dev:abc \n", DEV))


class EventStartTests(unittest.TestCase):
    def test_reads_the_ha_api_shapes_and_plain_values(self) -> None:
        self.assertEqual(
            calendar_tags.event_start({"start": {"dateTime": "2026-11-04T10:00:00+01:00"}}),
            datetime.datetime(2026, 11, 4, 10, 0),
        )
        self.assertEqual(calendar_tags.event_start({"start": {"date": "2026-11-04"}}), datetime.date(2026, 11, 4))
        self.assertEqual(
            calendar_tags.event_start({"start": datetime.datetime(2026, 11, 4, 9, 30)}),
            datetime.datetime(2026, 11, 4, 9, 30),
        )
        self.assertEqual(calendar_tags.event_start({"start": datetime.date(2026, 11, 4)}), datetime.date(2026, 11, 4))
        self.assertIsNone(calendar_tags.event_start({}))


if __name__ == "__main__":
    unittest.main()
