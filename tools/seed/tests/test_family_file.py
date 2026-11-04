"""The family file loader: the invented example loads, and every kind of bad file names its key."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from tools.seed import family_file
from tools.seed.family_file import EXAMPLE_FILE, FamilyFileError


def base() -> dict:
    """The example file as a fresh dict, ready to be broken one key at a time."""
    return copy.deepcopy(yaml.safe_load(EXAMPLE_FILE.read_text(encoding="utf-8")))


class ExampleFamilyTests(unittest.TestCase):
    def test_example_loads_with_the_invented_family(self) -> None:
        said: list[str] = []
        family = family_file.load(str(EXAMPLE_FILE), said.append)
        self.assertEqual([m.first_name for m in family.members], ["Sam", "Jordan", "Riley", "Casey"])
        self.assertEqual([m.username for m in family.members], ["sam", "jordan", "riley", "casey"])
        self.assertEqual([m.admin for m in family.members], [True, False, False, False])
        self.assertEqual([m.age for m in family.members], [None, None, 9, 6])
        self.assertTrue(all(m.local_calendar for m in family.members))
        self.assertEqual(family_file.her(family).first_name, "Jordan")
        self.assertEqual([m.first_name for m in family.children], ["Riley", "Casey"])
        self.assertIn(str(EXAMPLE_FILE), said[0])

    def test_load_says_which_file_it_used_and_missing_explicit_path_fails(self) -> None:
        with self.assertRaises(FamilyFileError) as caught:
            family_file.load("/nonexistent/family.yaml", lambda _line: None)
        self.assertIn("does not exist", str(caught.exception))

    def test_load_rejects_unreadable_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "family.yaml"
            path.write_text("members: [unclosed", encoding="utf-8")
            with self.assertRaises(FamilyFileError):
                family_file.load(str(path), lambda _line: None)

    def test_exit_code_is_two(self) -> None:
        self.assertEqual(FamilyFileError.exit_code, 2)


class BadFamilyTests(unittest.TestCase):
    def assertRejected(self, data: dict, *fragments: str) -> None:
        with self.assertRaises(FamilyFileError) as caught:
            family_file.parse(data)
        for fragment in fragments:
            self.assertIn(fragment, str(caught.exception))

    def test_unknown_top_level_key(self) -> None:
        data = base()
        data["extra"] = 1
        self.assertRejected(data, "extra")

    def test_unknown_member_key(self) -> None:
        data = base()
        data["members"][1]["nickname"] = "J"
        self.assertRejected(data, "members[1]", "nickname")

    def test_wrong_schema_version(self) -> None:
        data = base()
        data["schema_version"] = 2
        self.assertRejected(data, "schema_version")

    def test_two_admins(self) -> None:
        data = base()
        data["members"][1]["admin"] = True
        self.assertRejected(data, "exactly one", "admin")

    def test_no_admin(self) -> None:
        data = base()
        data["members"][0]["admin"] = False
        self.assertRejected(data, "exactly one", "admin")

    def test_admin_child(self) -> None:
        data = base()
        data["members"][2]["admin"] = True
        self.assertRejected(data, "members[2].admin")

    def test_no_non_admin_parent(self) -> None:
        data = base()
        del data["members"][1]
        self.assertRejected(data, "parent")

    def test_child_without_age(self) -> None:
        data = base()
        del data["members"][2]["age"]
        self.assertRejected(data, "members[2].age")

    def test_child_age_out_of_range(self) -> None:
        data = base()
        data["members"][2]["age"] = 2
        self.assertRejected(data, "members[2].age")

    def test_parent_with_age(self) -> None:
        data = base()
        data["members"][1]["age"] = 40
        self.assertRejected(data, "members[1].age")

    def test_bad_color(self) -> None:
        data = base()
        data["members"][0]["color"] = "blue"
        self.assertRejected(data, "members[0].color")

    def test_duplicate_names_differing_only_in_case(self) -> None:
        data = base()
        data["members"][3]["first_name"] = "riley"
        self.assertRejected(data, "members[3].first_name")

    def test_name_with_digits(self) -> None:
        data = base()
        data["members"][2]["first_name"] = "Riley2"
        self.assertRejected(data, "members[2].first_name")

    def test_login_name_may_not_collide(self) -> None:
        data = base()
        data["members"][3]["first_name"] = "Jor-dan"
        self.assertRejected(data, "members[3].first_name", "jordan")

    def test_tooling_login_is_reserved(self) -> None:
        data = base()
        data["members"][3]["first_name"] = "Fh Tools"
        self.assertRejected(data, "members[3].first_name", "fhtools")

    def test_google_calendar_while_google_block_is_null(self) -> None:
        data = base()
        data["members"][2]["calendar"] = "google:x"
        self.assertRejected(data, "members[2].calendar", "google")

    def test_google_block_needs_a_client_secret(self) -> None:
        data = base()
        data["google"] = {"client_id": "x"}
        self.assertRejected(data, "google.client_secret")


ICAL = "https://calendar.google.com/calendar/ical/family123%40group.calendar.google.com/private-0123abcd/basic.ics"


def with_google() -> dict:
    """The example family with a valid google block (two calendars) and Jordan on the first one."""
    data = base()
    data["members"][1]["calendar"] = "google:family"
    data["google"] = {
        "client_id": "test-client.apps.googleusercontent.com",
        "client_secret": "test-secret",
        "calendars": [
            {
                "key": "family",
                "calendar_id": "family123@group.calendar.google.com",
                "person": "Jordan",
                "writable": True,
                "expect_events": True,
                "backup": "ical",
                "ical_secret_url": ICAL,
            },
            {
                "key": "school-2",
                "calendar_id": "school456@group.calendar.google.com",
                "person": "Riley",
                "writable": False,
                "expect_events": False,
                "backup": "ha-snapshot",
            },
        ],
    }
    return data


class GoogleBlockTests(unittest.TestCase):
    """The google block (D-07, D-30): a valid one passes, and each mistake names its key path."""

    def assertRejected(self, data: dict, *fragments: str) -> None:
        with self.assertRaises(FamilyFileError) as caught:
            family_file.parse(data)
        for fragment in fragments:
            self.assertIn(fragment, str(caught.exception))

    def test_a_valid_block_passes_and_member_calendars_resolve(self) -> None:
        family = family_file.parse(with_google())
        self.assertEqual([c["key"] for c in family.google["calendars"]], ["family", "school-2"])
        self.assertEqual(family.member("Jordan").calendar, "google:family")
        self.assertFalse(family.member("Jordan").local_calendar)
        self.assertEqual(family.google["calendars"][1]["backup"], "ha-snapshot")

    def test_backup_defaults_to_ical_and_flags_default_to_false(self) -> None:
        data = with_google()
        for key in ("backup", "writable", "expect_events"):
            del data["google"]["calendars"][0][key]
        data["google"]["calendars"][0]["writable"] = True
        family = family_file.parse(data)
        calendar = family.google["calendars"][0]
        self.assertEqual(calendar["backup"], "ical")
        self.assertIs(calendar["expect_events"], False)

    def test_missing_client_id(self) -> None:
        data = with_google()
        del data["google"]["client_id"]
        self.assertRejected(data, "google.client_id")

    def test_missing_client_secret(self) -> None:
        data = with_google()
        data["google"]["client_secret"] = ""
        self.assertRejected(data, "google.client_secret")

    def test_unknown_google_key(self) -> None:
        data = with_google()
        data["google"]["token"] = "x"
        self.assertRejected(data, "google", "token")

    def test_calendar_key_with_upper_case(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["key"] = "Family"
        self.assertRejected(data, "google.calendars[0].key")

    def test_calendar_key_with_a_space(self) -> None:
        data = with_google()
        data["google"]["calendars"][1]["key"] = "my school"
        self.assertRejected(data, "google.calendars[1].key")

    def test_duplicate_calendar_key(self) -> None:
        data = with_google()
        data["google"]["calendars"][1]["key"] = "family"
        self.assertRejected(data, "google.calendars[1].key", "family")

    def test_person_that_is_not_a_member(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["person"] = "Nobody"
        self.assertRejected(data, "google.calendars[0].person", "Nobody")

    def test_member_calendar_with_no_such_key(self) -> None:
        data = with_google()
        data["members"][2]["calendar"] = "google:nope"
        self.assertRejected(data, "members[2].calendar", "nope")

    def test_ical_backup_without_a_secret_address(self) -> None:
        data = with_google()
        del data["google"]["calendars"][0]["ical_secret_url"]
        self.assertRejected(data, "google.calendars[0].ical_secret_url")

    def test_secret_address_must_be_on_calendar_google_com(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["ical_secret_url"] = "https://example.com/calendar/ical/x/private-1/basic.ics"
        self.assertRejected(data, "google.calendars[0].ical_secret_url", "calendar.google.com")

    def test_secret_address_must_end_in_ics(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["ical_secret_url"] = "https://calendar.google.com/calendar/ical/x/private-1/basic"
        self.assertRejected(data, "google.calendars[0].ical_secret_url", ".ics")

    def test_secret_address_must_be_https(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["ical_secret_url"] = ICAL.replace("https://", "http://")
        self.assertRejected(data, "google.calendars[0].ical_secret_url")

    def test_a_snapshot_calendar_needs_no_secret_address(self) -> None:
        family = family_file.parse(with_google())
        self.assertNotIn("ical_secret_url", family.google["calendars"][1])

    def test_secret_address_is_never_part_of_an_error_message(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["ical_secret_url"] = "https://example.com/private-SECRETTOKEN/basic.ics"
        with self.assertRaises(FamilyFileError) as caught:
            family_file.parse(data)
        self.assertNotIn("SECRETTOKEN", str(caught.exception))

    def test_duplicate_calendar_id(self) -> None:
        data = with_google()
        data["google"]["calendars"][1]["calendar_id"] = "family123@group.calendar.google.com"
        self.assertRejected(data, "google.calendars[1].calendar_id")

    def test_expecting_events_on_a_read_only_calendar(self) -> None:
        data = with_google()
        data["google"]["calendars"][1]["expect_events"] = True
        self.assertRejected(data, "google.calendars[1].expect_events")

    def test_unknown_backup_kind(self) -> None:
        data = with_google()
        data["google"]["calendars"][1]["backup"] = "dropbox"
        self.assertRejected(data, "google.calendars[1].backup")

    def test_flags_must_be_booleans(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["writable"] = "yes"
        self.assertRejected(data, "google.calendars[0].writable")

    def test_unknown_calendar_key_name(self) -> None:
        data = with_google()
        data["google"]["calendars"][0]["colour"] = "red"
        self.assertRejected(data, "google.calendars[0]", "colour")

    def test_calendar_id_is_required(self) -> None:
        data = with_google()
        del data["google"]["calendars"][0]["calendar_id"]
        self.assertRejected(data, "google.calendars[0].calendar_id")

    def test_a_google_block_without_calendars_is_allowed_but_empty(self) -> None:
        data = with_google()
        data["google"]["calendars"] = []
        data["members"][1]["calendar"] = "local"
        self.assertEqual(family_file.parse(data).google["calendars"], [])


if __name__ == "__main__":
    unittest.main()
