"""Live tests for the Preview scripts' Python side, on a real Home Assistant 2026.10.4.

Port 18133 belongs to this module, target "preview". Each class boots its own Home Assistant, so a
test that wipes or mutates the instance cannot disturb another.

Run: FH_HASS=$HOME/.cache/fh-hassfest/venv/bin/hass python -B -m unittest discover \
        -s tools/seed/tests -t . -p 'live_preview.py' -v
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.seed import deploy, resources

from .live_ha import REPO_ROOT, LiveHA

PORT = 18133


def export_head(out: Path) -> dict[str, str]:
    """Export HEAD the way deploy-preview does (fh_export_build) and return the build file's keys."""
    result = subprocess.run(
        ["bash", "-c", '. scripts/lib.sh\nfh_export_build HEAD "$1" Preview', "_", str(out)],
        cwd=REPO_ROOT,
        env=dict(os.environ, TZ="Europe/London"),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("export failed: %s" % result.stderr)
    shown = subprocess.run(
        [
            "bash",
            "-c",
            '. "$1"; printf "%s\\n" "$FH_SHA" "$FH_SHORT" "$FH_VERSION" "$FH_DEPLOYED" "$FH_STAMP"',
            "_",
            str(out / "fh-build.env"),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return dict(zip(("FH_SHA", "FH_SHORT", "FH_VERSION", "FH_DEPLOYED", "FH_STAMP"), shown))


class LiveDeployTests(unittest.TestCase):
    """verify-served and note against a Preview running an exported, stamped copy of HEAD."""

    ha: LiveHA
    build: dict[str, str]
    served_dir: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "export"
        cls.build = export_head(out)
        cls.ha = LiveHA("preview", PORT, integration_src=str(out / "custom_components" / "family_hub"))
        cls.ha.__enter__()
        cls.served_dir = str(cls.ha.config_dir / "custom_components" / "family_hub")
        try:
            cls.first = cls.ha.seed("seed", "--integration-dir", cls.served_dir)
        except BaseException:
            cls.ha.__exit__(None, None, None)
            cls.tmp.cleanup()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ha.__exit__(None, None, None)
        cls.tmp.cleanup()

    def verify_served(self, expect: str) -> subprocess.CompletedProcess:
        return self.ha.seed("verify-served", "--expect", expect, "--integration-dir", self.served_dir)

    def test_a_seed_of_the_stamped_copy_passes_its_own_verify(self) -> None:
        self.assertEqual(self.first.returncode, 0, self.first.stdout + self.first.stderr)
        self.assertIn("verify: all", self.first.stdout)

    def test_b_the_served_card_carries_the_short_hash_and_the_full_stamp(self) -> None:
        stamp = self.build["FH_STAMP"]
        result = self.verify_served(stamp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("served: %s OK" % stamp, result.stdout)

        async def fetch(client, token, _ws):
            return await client.rest("GET", deploy.CARD_URL, token=token)

        status, body = self.ha.run_async(self._admin(fetch))
        self.assertEqual(status, 200)
        self.assertIn(self.build["FH_SHORT"], body)
        self.assertNotIn("__FH_BUILD_VERSION__", body)

    def _admin(self, fn):
        async def run():
            async with self.ha.admin_session() as (client, token, ws):
                return await fn(client, token, ws)

        return run()

    def test_c_a_second_run_passes_and_there_is_one_resource_per_card_path(self) -> None:
        again = self.verify_served(self.build["FH_STAMP"])
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)

        async def read(_client, _token, ws):
            return (await ws.call("lovelace/resources"))["result"]

        rows = self.ha.run_async(self._admin(read))
        served = resources.served_js_files(self.served_dir)
        paths = [row["url"].split("?", 1)[0].rsplit("/", 1)[-1] for row in rows]
        for name in set(paths):
            self.assertEqual(paths.count(name), 1, "more than one resource for %s" % name)
        self.assertTrue(set(paths) <= set(served), set(paths) - set(served))
        self.assertIn("family-week-calendar-card.js", paths)
        for row in rows:
            name = row["url"].split("?", 1)[0].rsplit("/", 1)[-1]
            self.assertTrue(row["url"].endswith("?v=" + resources.content_hash(served[name])), row["url"])

    def test_d_a_stamp_that_was_not_deployed_fails(self) -> None:
        result = self.verify_served("Preview · 9.9.9+deadbee · 1 Jan 00:00")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("not serving", result.stderr)

    def test_e_a_malformed_stamp_fails_without_touching_anything(self) -> None:
        result = self.verify_served("Preview - 1.0 - now")
        self.assertEqual(result.returncode, 1)

    def test_f_note_prints_the_ready_line_and_the_served_stamp(self) -> None:
        result = self.ha.seed(
            "note",
            "--stamp=" + self.build["FH_STAMP"],
            "--what=Chores now show their stars.",
            "--view=Chores",
            "--tap=the first chore",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "Preview is updated and ready for you to try.")
        self.assertIn('"%s".' % self.build["FH_STAMP"], result.stdout)
        self.assertTrue(all(len(line) <= 72 for line in lines))


if __name__ == "__main__":
    unittest.main()
