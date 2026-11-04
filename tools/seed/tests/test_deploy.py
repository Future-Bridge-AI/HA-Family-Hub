"""Unit tests for the deploy side: the hand-off note, the served-card check and the export + stamp.

No Home Assistant and no Docker: verify_served runs against a fake client, and the export runs
scripts/lib.sh against this repository's own HEAD in a temp directory.

Run: python -B -m unittest discover -s tools/seed/tests -t . -p 'test_*.py' -v
"""
from __future__ import annotations

import asyncio
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.seed import deploy, resources
from tools.seed.client import SeedError

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION = str(REPO_ROOT / "custom_components" / "family_hub")
MIDDOT = "·"
STAMP = "Preview %s 2.0.0+a1b2c3d %s 27 Oct 14:05" % (MIDDOT, MIDDOT)


class HandoffNoteTests(unittest.TestCase):
    def test_every_line_is_at_most_72_code_points_with_real_values(self) -> None:
        lines = deploy.handoff_note(
            STAMP,
            what="Chores now show how many stars each one is worth, next to the name.",
            view="Chores",
            tap="the first chore on Riley's list",
        )
        self.assertTrue(lines)
        for line in lines:
            self.assertLessEqual(len(line), 72, line)

    def test_every_line_is_at_most_72_code_points_with_every_fallback(self) -> None:
        for line in deploy.handoff_note(STAMP):
            self.assertLessEqual(len(line), 72, line)

    def test_exact_shape_with_real_values(self) -> None:
        lines = deploy.handoff_note(STAMP, what="Chores show their stars.", view="Chores", tap="a chore")
        self.assertEqual(
            lines,
            [
                "Preview is updated and ready for you to try.",
                "",
                "What changed:  Chores show their stars.",
                "Where to look: Open Family Hub PREVIEW, tap Chores, then a chore.",
                "Check it is new: the small line at the bottom of the Calendar should say",
                '                 "Preview %s 2.0.0+a1b2c3d %s 27 Oct 14:05".' % (MIDDOT, MIDDOT),
            ],
        )

    def test_fallback_strings_match_the_contract_exactly(self) -> None:
        lines = deploy.handoff_note(STAMP)
        self.assertIn("What changed:  (no note was given - tell her what changed yourself)", lines)
        self.assertIn("Where to look: Open Family Hub PREVIEW.", lines)
        self.assertIn(" " * 17 + "(no screen was given - tell her where to tap yourself)", lines)
        self.assertNotIn("Preview is updated and ready for you to try.", lines[1:])  # printed once, first
        self.assertEqual(lines[0], "Preview is updated and ready for you to try.")

    def test_a_blank_note_is_the_fallback_too(self) -> None:
        self.assertEqual(deploy.handoff_note(STAMP, what="   ", view="", tap=None), deploy.handoff_note(STAMP))

    def test_only_a_view_or_only_a_tap_still_reads_as_a_sentence(self) -> None:
        self.assertIn("Where to look: Open Family Hub PREVIEW, tap Rewards.", deploy.handoff_note(STAMP, view="Rewards"))
        self.assertIn(
            "Where to look: Open Family Hub PREVIEW, then the star button.", deploy.handoff_note(STAMP, tap="the star button")
        )

    def test_a_200_character_note_is_wrapped_and_never_cut_off(self) -> None:
        what = " ".join(["Chores"] * 33)[:200].rstrip()
        self.assertGreaterEqual(len(what), 190)
        lines = deploy.handoff_note(STAMP, what=what)
        start = lines.index(next(line for line in lines if line.startswith("What changed:")))
        end = lines.index(next(line for line in lines if line.startswith("Where to look:")))
        block = lines[start:end]
        self.assertGreaterEqual(len(block), 3)
        for line in block:
            self.assertLessEqual(len(line), 72)
        self.assertEqual(" ".join(part.strip() for part in block).replace("What changed:", "", 1).split(), what.split())
        for line in block[1:]:
            self.assertTrue(line.startswith(" " * 17) and not line.startswith(" " * 18), line)

    def test_a_single_very_long_word_is_split_rather_than_overflowing(self) -> None:
        what = "x" * 300
        lines = deploy.handoff_note(STAMP, what=what)
        for line in lines:
            self.assertLessEqual(len(line), 72, line)
        text = "\n".join(lines)
        self.assertEqual(text.count("x"), 300)

    def test_new_lines_in_the_note_do_not_break_the_one_sentence_shape(self) -> None:
        lines = deploy.handoff_note(STAMP, what="First part\nsecond part.", view="Chores\n", tap="a\tchore")
        text = "\n".join(lines)
        self.assertIn("What changed:  First part second part.", text)
        self.assertIn("tap Chores, then a chore.", text)

    def test_the_separator_is_a_middle_dot_with_one_space_either_side(self) -> None:
        self.assertEqual(deploy.STAMP_SEPARATOR, " · ")
        self.assertEqual(deploy.STAMP_SEPARATOR.encode("utf-8"), b" \xc2\xb7 ")
        note = "\n".join(deploy.handoff_note(STAMP))
        self.assertEqual(note.count("·"), 2)

    def test_length_is_counted_in_code_points_not_bytes(self) -> None:
        # A 72 code point line that is 74 bytes (two middle dots) must be allowed to stay on one line.
        stamp = "Preview %s %s %s %s" % (MIDDOT, "v" * 12, MIDDOT, "t" * 12)
        line = deploy.handoff_note(stamp)[-1]
        self.assertEqual(line, " " * 17 + '"%s".' % stamp)
        self.assertGreater(len(line.encode("utf-8")), len(line))

    def test_a_stamp_that_is_not_three_parts_is_refused(self) -> None:
        for bad in ("Preview - 2.0.0+abc - 1 Jan 00:00", "Preview %s 2.0.0+abc" % MIDDOT, "", "a %s %s c" % (MIDDOT, "")):
            with self.assertRaises(SeedError, msg=bad):
                deploy.handoff_note(bad)


class ServedCardTests(unittest.TestCase):
    BODY = (
        "// card\nconst __FH_BUILD = { env: \"Preview\", version: \"2.0.0+a1b2c3d\", deployed: \"27 Oct 14:05\" };\nmore();\n"
    )

    def test_a_matching_card_has_no_problems(self) -> None:
        self.assertEqual(deploy.check_served_card(self.BODY, STAMP), [])

    def test_each_part_of_the_stamp_is_checked(self) -> None:
        for wrong in (
            "Dev %s 2.0.0+a1b2c3d %s 27 Oct 14:05" % (MIDDOT, MIDDOT),
            "Preview %s 2.0.0+ffffffff %s 27 Oct 14:05" % (MIDDOT, MIDDOT),
            "Preview %s 2.0.0+a1b2c3d %s 28 Oct 14:05" % (MIDDOT, MIDDOT),
        ):
            self.assertEqual(len(deploy.check_served_card(self.BODY, wrong)), 1, wrong)

    def test_a_leftover_placeholder_is_a_problem(self) -> None:
        body = self.BODY + '// version: "__FH_BUILD_VERSION__"\n'
        problems = deploy.check_served_card(body, STAMP)
        self.assertEqual(len(problems), 1)
        self.assertIn("__FH_BUILD_VERSION__", problems[0])

    def test_a_card_without_a_build_line_or_not_text_is_a_problem(self) -> None:
        self.assertTrue(deploy.check_served_card("nothing here", STAMP))
        self.assertTrue(deploy.check_served_card(None, STAMP))


class FakeWS:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    async def call(self, command: str, **_kw) -> dict:
        assert command == "lovelace/resources"
        return {"result": self.rows}


class FakeClient:
    def __init__(self, status: int, body: object, rows: list[dict]) -> None:
        self.reply = (status, body)
        self.rows = rows
        self.paths: list[str] = []

    async def rest(self, method: str, path: str, **_kw):
        self.paths.append(path)
        return self.reply

    async def ws(self, _token: str) -> FakeWS:
        return FakeWS(self.rows)


def good_resources() -> list[dict]:
    files = resources.served_js_files(INTEGRATION)
    urls = resources.served_urls(INTEGRATION)
    rows = []
    for index, (name, path) in enumerate(sorted(files.items())):
        if name in urls:
            rows.append({"id": "r%d" % index, "url": "%s?v=%s" % (urls[name], resources.content_hash(path))})
    return rows


class VerifyServedTests(unittest.TestCase):
    def run_verify(self, client: FakeClient, expect: str = STAMP) -> list[str]:
        out: list[str] = []
        asyncio.run(deploy.verify_served(client, "token", INTEGRATION, expect, out.append))
        return out

    def test_matching_card_and_resources_print_ok(self) -> None:
        client = FakeClient(200, ServedCardTests.BODY, good_resources())
        self.assertEqual(self.run_verify(client), ["served: %s OK" % STAMP])
        self.assertEqual(client.paths, [deploy.CARD_URL])

    def test_a_wrong_stamp_raises_and_names_the_problem(self) -> None:
        client = FakeClient(200, ServedCardTests.BODY, good_resources())
        wrong = "Preview %s 9.9.9+deadbee %s 1 Jan 00:00" % (MIDDOT, MIDDOT)
        with self.assertRaises(SeedError) as caught:
            self.run_verify(client, wrong)
        self.assertEqual(caught.exception.code, "not_served")
        self.assertIn("9.9.9+deadbee", caught.exception.message)

    def test_a_stale_resource_is_a_problem(self) -> None:
        rows = good_resources()
        rows[0] = dict(rows[0], url=rows[0]["url"].split("?")[0] + "?v=0000000000")
        with self.assertRaises(SeedError) as caught:
            self.run_verify(FakeClient(200, ServedCardTests.BODY, rows))
        self.assertIn("stale", caught.exception.message)

    def test_two_resources_for_one_path_is_a_problem(self) -> None:
        rows = good_resources()
        rows.append(dict(rows[0], id="extra"))
        with self.assertRaises(SeedError) as caught:
            self.run_verify(FakeClient(200, ServedCardTests.BODY, rows))
        self.assertIn("duplicate", caught.exception.message)

    def test_a_missing_resource_is_a_problem(self) -> None:
        with self.assertRaises(SeedError) as caught:
            self.run_verify(FakeClient(200, ServedCardTests.BODY, good_resources()[1:]))
        self.assertIn("no resource for", caught.exception.message)

    def test_a_card_that_is_not_served_is_a_problem(self) -> None:
        with self.assertRaises(SeedError) as caught:
            self.run_verify(FakeClient(404, "not found", good_resources()))
        self.assertIn("HTTP 404", caught.exception.message)


class ExportBuildTests(unittest.TestCase):
    CARD = "custom_components/family_hub/card/family-week-calendar-card.js"
    TOKENS = ("__FH_BUILD_ENV__", "__FH_BUILD_VERSION__", "__FH_BUILD_TIME__")

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "out"

    def export(self, ref: str = "HEAD", word: str = "Preview") -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", "-c", '. scripts/lib.sh\nfh_export_build "$1" "$2" "$3"', "_", ref, str(self.out), word],
            cwd=REPO_ROOT,
            env=dict(os.environ, TZ="Europe/London"),
            capture_output=True,
            text=True,
        )

    def test_the_exported_card_is_stamped_and_the_repo_copy_is_not(self) -> None:
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        card = (self.out / self.CARD).read_text(encoding="utf-8")
        for token in self.TOKENS:
            self.assertNotIn(token, card)
        line = next(line for line in card.splitlines() if line.startswith("const __FH_BUILD ="))
        manifest = (self.out / "custom_components/family_hub/manifest.json").read_text(encoding="utf-8")
        version = re.search(r'"version"\s*:\s*"([^"]+)"', manifest).group(1)
        self.assertRegex(line, r'env: "Preview"')
        self.assertRegex(line, r'version: "%s\+[0-9a-f]{7}"' % re.escape(version))
        deployed = re.search(r'deployed: "([^"]+)"', line).group(1)
        self.assertRegex(deployed, r"^[1-9][0-9]? [A-Z][a-z]{2} [0-2][0-9]:[0-5][0-9]$")
        repo_card = (REPO_ROOT / self.CARD).read_text(encoding="utf-8")
        for token in self.TOKENS:
            self.assertEqual(repo_card.count(token), 1, "the repo copy of the card must keep %s" % token)

    def test_the_build_file_has_the_five_keys_and_a_middle_dot_stamp(self) -> None:
        self.assertEqual(self.export().returncode, 0)
        env_file = self.out / "fh-build.env"
        keys = [line.split("=", 1)[0] for line in env_file.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(keys, ["FH_SHA", "FH_SHORT", "FH_VERSION", "FH_DEPLOYED", "FH_STAMP"])
        shown = subprocess.run(
            ["bash", "-c", '. "$1"; printf "%s\\n" "$FH_SHA" "$FH_SHORT" "$FH_VERSION" "$FH_DEPLOYED" "$FH_STAMP"', "_", str(env_file)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        sha, short, version, deployed, stamp = shown
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertEqual(short, sha[:7])
        self.assertEqual(stamp, "Preview %s %s+%s %s %s" % (MIDDOT, version, short, MIDDOT, deployed))
        self.assertEqual(deploy.parse_stamp(stamp), ("Preview", "%s+%s" % (version, short), deployed))

    def test_the_stamp_in_the_build_file_is_what_verify_served_expects_in_the_card(self) -> None:
        self.assertEqual(self.export().returncode, 0)
        env_file = self.out / "fh-build.env"
        stamp = subprocess.run(
            ["bash", "-c", '. "$1"; printf "%s" "$FH_STAMP"', "_", str(env_file)], capture_output=True, text=True, check=True
        ).stdout
        card = (self.out / self.CARD).read_text(encoding="utf-8")
        self.assertEqual(deploy.check_served_card(card, stamp), [])

    def test_an_unknown_ref_fails_and_writes_nothing(self) -> None:
        result = self.export(ref="no-such-branch-anywhere")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not resolve", result.stderr)
        self.assertFalse(self.out.exists())

    def test_an_environment_word_with_odd_characters_is_refused_before_anything_is_written(self) -> None:
        result = self.export(word="Pre|view")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
