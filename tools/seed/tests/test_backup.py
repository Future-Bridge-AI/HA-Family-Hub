"""The calendar backup (D-08, D-30): a valid dated .ics per chosen calendar, or a hard stop naming the key.

The fetcher and the snapshot reader are injected, so nothing here touches the network or Home Assistant.
The secret iCal address of a calendar must never appear in any output.
"""
from __future__ import annotations

import contextlib
import copy
import datetime
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from tools.seed import backup as backup_mod
from tools.seed import family_file
from tools.seed.__main__ import main
from tools.seed.backup import BackupError
from tools.seed.envs import ENVIRONMENTS

SECRET = "private-SECRETTOKEN0123"
URL_FAMILY = "https://calendar.google.com/calendar/ical/family123%%40group.calendar.google.com/%s/basic.ics" % SECRET
URL_SCHOOL = "https://calendar.google.com/calendar/ical/school456%%40group.calendar.google.com/%s-2/basic.ics" % SECRET
VALID = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:1\r\nSUMMARY:Dentist\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
NOW = datetime.datetime(2026, 11, 4, 14, 5, 9)
STAMP = "2026-11-04_140509"


def family(snapshot_school: bool = False):
    data = yaml.safe_load(family_file.EXAMPLE_FILE.read_text(encoding="utf-8"))
    calendars = [
        {
            "key": "family",
            "calendar_id": "family123@group.calendar.google.com",
            "person": "Jordan",
            "writable": True,
            "expect_events": True,
            "backup": "ical",
            "ical_secret_url": URL_FAMILY,
        },
        {
            "key": "school",
            "calendar_id": "school456@group.calendar.google.com",
            "person": "Riley",
            "writable": False,
            "expect_events": False,
            **({"backup": "ha-snapshot"} if snapshot_school else {"backup": "ical", "ical_secret_url": URL_SCHOOL}),
        },
    ]
    data["google"] = {"client_id": "test-client.apps.googleusercontent.com", "client_secret": "s", "calendars": calendars}
    return family_file.parse(data), data


def ok_fetch(url: str):
    return 200, VALID


class BackupCalendarsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.join(self._tmp.name, ".ha-backups")

    def run_backup(self, fam, fetch=ok_fetch, snapshot=None, env="dev") -> str:
        return backup_mod.backup_calendars(fam, ENVIRONMENTS[env], self.root, NOW, fetch, snapshot)

    def stamp_dir(self, env="dev") -> Path:
        return Path(self.root) / env / STAMP

    def test_writes_one_private_ics_per_ical_calendar_in_a_dated_folder(self) -> None:
        fam, _ = family()
        line = self.run_backup(fam)
        self.assertEqual(line, "backup: 2 calendars -> %s" % os.path.join(self.root, "dev", STAMP))
        for key in ("family", "school"):
            path = self.stamp_dir() / ("%s.ics" % key)
            self.assertEqual(path.read_bytes().decode("utf-8"), VALID, "stored exactly as Google sent it")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.stamp_dir().stat().st_mode), 0o700)
        self.assertEqual(sorted(p.name for p in self.stamp_dir().iterdir()), ["family.ics", "school.ics"])

    def test_each_calendar_is_fetched_from_its_own_secret_address(self) -> None:
        fam, _ = family()
        fetched: list[str] = []

        def fetch(url: str):
            fetched.append(url)
            return 200, VALID

        self.run_backup(fam, fetch=fetch)
        self.assertEqual(fetched, [URL_FAMILY, URL_SCHOOL])

    def test_dev_and_preview_back_up_into_separate_folders(self) -> None:
        fam, _ = family()
        self.run_backup(fam, env="dev")
        self.run_backup(fam, env="preview")
        self.assertTrue((Path(self.root) / "dev" / STAMP / "family.ics").exists())
        self.assertTrue((Path(self.root) / "preview" / STAMP / "family.ics").exists())

    def assertStops(self, fam, fetch, key: str, *words: str, snapshot=None) -> BackupError:
        with self.assertRaises(BackupError) as caught:
            self.run_backup(fam, fetch=fetch, snapshot=snapshot)
        message = str(caught.exception)
        self.assertIn("backup failed for %s" % key, message)
        self.assertIn("nothing was changed", message)
        for word in words:
            self.assertIn(word, message)
        self.assertNotIn(SECRET, message)
        self.assertFalse((Path(self.root) / "dev" / STAMP).exists(), "no dated folder is left behind")
        return caught.exception

    def test_http_404_stops_and_names_the_key(self) -> None:
        fam, _ = family()
        self.assertStops(fam, lambda url: (404, "Not Found"), "family", "404")

    def test_an_empty_body_stops(self) -> None:
        fam, _ = family()
        self.assertStops(fam, lambda url: (200, ""), "family", "empty")

    def test_a_body_that_is_not_a_calendar_stops(self) -> None:
        fam, _ = family()
        self.assertStops(fam, lambda url: (200, "<html><body>Sign in</body></html>"), "family", "BEGIN:VCALENDAR")

    def test_a_calendar_cut_off_before_its_end_stops(self) -> None:
        fam, _ = family()
        truncated = VALID.replace("END:VCALENDAR\r\n", "")
        self.assertStops(fam, lambda url: (200, truncated), "family", "END:VCALENDAR")

    def test_a_fetch_that_raises_stops_without_echoing_the_exception_text(self) -> None:
        fam, _ = family()

        def boom(url: str):
            raise OSError("connection refused for %s" % url)

        error = self.assertStops(fam, boom, "family", "OSError")
        self.assertNotIn("connection refused", str(error))

    def test_one_bad_calendar_among_good_ones_leaves_no_partial_backup(self) -> None:
        fam, _ = family()

        def second_is_bad(url: str):
            return (200, VALID) if url == URL_FAMILY else (404, "")

        self.assertStops(fam, second_is_bad, "school", "404")
        self.assertEqual(list((Path(self.root) / "dev").iterdir()) if (Path(self.root) / "dev").exists() else [], [])

    def test_a_snapshot_calendar_is_written_as_json_through_the_injected_reader(self) -> None:
        fam, _ = family(snapshot_school=True)
        seen: list[str] = []

        def snapshot(calendar: dict):
            seen.append(calendar["key"])
            return {"events": [{"summary": "Dentist"}]}

        line = self.run_backup(fam, snapshot=snapshot)
        self.assertEqual(seen, ["school"])
        self.assertIn("2 calendars", line)
        path = self.stamp_dir() / "school.json"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["events"], [{"summary": "Dentist"}])
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertTrue((self.stamp_dir() / "family.ics").exists())

    def test_an_unavailable_snapshot_stops(self) -> None:
        fam, _ = family(snapshot_school=True)
        self.assertStops(fam, ok_fetch, "school", "snapshot", snapshot=lambda calendar: None)
        self.assertStops(fam, ok_fetch, "school", "snapshot", snapshot=None)

    def test_a_snapshot_reader_that_raises_stops(self) -> None:
        fam, _ = family(snapshot_school=True)

        def broken(calendar: dict):
            raise RuntimeError("Home Assistant is down")

        self.assertStops(fam, ok_fetch, "school", "snapshot", snapshot=broken)

    def test_no_google_block_writes_nothing(self) -> None:
        fam = family_file.load(str(family_file.EXAMPLE_FILE), lambda _line: None)
        self.assertEqual(self.run_backup(fam), "backup: no Google calendars configured")
        self.assertFalse(os.path.exists(self.root))

    def test_a_google_block_without_calendars_writes_nothing(self) -> None:
        _fam, data = family()
        data["google"]["calendars"] = []
        data["members"][1]["calendar"] = "local"
        fam = family_file.parse(copy.deepcopy(data))
        self.assertEqual(self.run_backup(fam), "backup: no Google calendars configured")
        self.assertFalse(os.path.exists(self.root))

    def test_two_backups_in_the_same_second_do_not_overwrite_each_other(self) -> None:
        fam, _ = family()
        self.run_backup(fam)
        self.run_backup(fam)
        self.assertEqual(len(list((Path(self.root) / "dev").iterdir())), 2)

    def test_the_secret_address_is_only_used_to_fetch_never_formatted(self) -> None:
        text = Path(backup_mod.__file__).read_text(encoding="utf-8")
        self.assertIn("ical_secret_url", text)
        for line in text.splitlines():
            if "ical_secret_url" in line:
                self.assertNotRegex(line, r"(print|say|_LOGGER\.\w+|%s|format\()", line)


class BackupCommandTests(unittest.TestCase):
    """The seed subcommand: exit codes and the promise that the secret address is never printed."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        _fam, data = family()
        self.family_path = tmp / "family.yaml"
        self.family_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        self.root = str(tmp / "backups")

    def run_main(self, fetch):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(backup_mod, "default_fetch", fetch), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(
                ["--target", "dev", "--secrets-dir", str(Path(self._tmp.name) / "secrets"), "backup-calendars",
                 "--family", str(self.family_path), "--backups-dir", self.root]
            )
        return code, out.getvalue(), err.getvalue()

    def test_success_exits_zero_and_prints_the_count_and_folder(self) -> None:
        code, out, err = self.run_main(ok_fetch)
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"backup: 2 calendars -> .*/dev/\d{4}-\d\d-\d\d_\d{6}")
        self.assertNotIn(SECRET, out + err)

    def test_a_bad_calendar_exits_five_with_the_plain_message(self) -> None:
        code, out, err = self.run_main(lambda url: (404, ""))
        self.assertEqual(code, 5)
        self.assertIn("backup failed for family: ", err)
        self.assertIn(" - nothing was changed", err)
        self.assertNotIn(SECRET, out + err)
        self.assertFalse(os.path.exists(os.path.join(self.root, "dev")) and os.listdir(os.path.join(self.root, "dev")))

    def test_the_family_file_without_a_google_block_is_a_quiet_success(self) -> None:
        plain = Path(self._tmp.name) / "plain.yaml"
        plain.write_text(family_file.EXAMPLE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        self.family_path = plain
        code, out, err = self.run_main(lambda url: self.fail("no fetch without a google block"))
        self.assertEqual(code, 0, err)
        self.assertIn("backup: no Google calendars configured", out)


if __name__ == "__main__":
    unittest.main()
