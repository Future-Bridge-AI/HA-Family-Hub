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


if __name__ == "__main__":
    unittest.main()
