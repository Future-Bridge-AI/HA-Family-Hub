"""Live tests for the Preview scripts' Python side, on a real Home Assistant 2026.10.4.

Port 18133 belongs to this module, target "preview". Each class boots its own Home Assistant, so a
test that wipes or mutates the instance cannot disturb another.

Run: FH_HASS=$HOME/.cache/fh-hassfest/venv/bin/hass python -B -m unittest discover \
        -s tools/seed/tests -t . -p 'live_preview.py' -v
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.seed import deploy, resources
from tools.seed.client import HAClient

from .live_ha import REPO_ROOT, LiveHA

PORT = 18133


def export_head(out: Path, deployed: str = "") -> dict[str, str]:
    """Export HEAD the way deploy-preview does (fh_export_build) and return the build file's keys.

    ``deployed`` fixes the deploy time (a stub ``date`` for the build-time format only), so two
    exports of the same commit can be told apart.
    """
    env = dict(os.environ, TZ="Europe/London")
    if deployed:
        stub_dir = out.parent / ("bin-" + out.name)
        stub_dir.mkdir(parents=True, exist_ok=True)
        stub = stub_dir / "date"
        stub.write_text(
            '#!/usr/bin/env bash\nif [ "$1" = "+%e %b %H:%M" ]; then printf \'%s\\n\' "' + deployed + '"; exit 0; fi\n'
            'exec /bin/date "$@"\n',
            encoding="utf-8",
        )
        stub.chmod(0o755)
        env["PATH"] = "%s:%s" % (stub_dir, env["PATH"])
    result = subprocess.run(
        ["bash", "-c", '. scripts/lib.sh\nfh_export_build HEAD "$1" Preview', "_", str(out)],
        cwd=REPO_ROOT,
        env=env,
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

    def test_g_deploying_the_same_commit_again_keeps_one_resource_per_card_path(self) -> None:
        """PREV-07 idempotency: same version and hash, a newer time, still one resource per card."""
        first_stamp = self.build["FH_STAMP"]
        second_build = export_head(Path(self.tmp.name) / "export2", deployed="31 Dec 23:59")
        self.assertEqual(second_build["FH_SHA"], self.build["FH_SHA"])
        self.assertNotEqual(second_build["FH_STAMP"], first_stamp)
        self.assertEqual(second_build["FH_STAMP"].split(" \u00b7 ")[:2], first_stamp.split(" \u00b7 ")[:2])

        # What deploy-preview does on disk: stop, swap the exported copy in, start, seed, verify.
        self.ha.stop()
        live = self.ha.config_dir / "custom_components" / "family_hub"
        shutil.rmtree(live)
        shutil.copytree(Path(self.tmp.name) / "export2" / "custom_components" / "family_hub", live)
        self.ha.start()
        seeded = self.ha.seed("seed", "--integration-dir", self.served_dir)
        self.assertEqual(seeded.returncode, 0, seeded.stdout + seeded.stderr)
        again = self.verify_served(second_build["FH_STAMP"])
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(self.verify_served(first_stamp).returncode, 1)

        async def read(_client, _token, ws):
            return (await ws.call("lovelace/resources"))["result"]

        rows = self.ha.run_async(self._admin(read))
        paths = [row["url"].split("?", 1)[0] for row in rows]
        self.assertEqual(len(paths), len(set(paths)), paths)


class LiveResetTests(unittest.TestCase):
    """PREV-06: after a reset none of her earlier data comes back, and her login still works.

    One boot, one sequence in setUpClass (seed, mutate, stop, wipe through lib.sh, re-render the
    configuration, start, seed); the tests read what was recorded along the way.
    """

    ha: LiveHA
    served_dir: str
    CHILD = "Riley"
    HER = "Jordan"

    @classmethod
    def setUpClass(cls) -> None:
        cls.ha = LiveHA("preview", PORT)
        cls.ha.__enter__()
        try:
            cls.served_dir = str(cls.ha.config_dir / "custom_components" / "family_hub")
            cls.first = cls.ha.seed("seed", "--integration-dir", cls.served_dir)
            if cls.first.returncode != 0:
                raise RuntimeError("first seed failed: %s %s" % (cls.first.stdout, cls.first.stderr))
            cls.fresh = cls.ha.run_async(cls._admin_call(cls.read_state))
            cls.child_id = cls.ha.run_async(cls._admin_call(cls.find_user, cls.CHILD))
            cls.mutated = cls.ha.run_async(cls._admin_call(cls.mutate))
            cls.config = cls.ha.config_dir
            cls.before_wipe = {
                "storage": (cls.config / ".storage").is_dir(),
                "backups": (cls.config / "family_hub_backups").is_dir(),
                "after_mutation": cls.ha.run_async(cls._admin_call(cls.read_state)),
            }
            cls.ha.stop()
            cls.wipe = cls.ha.wipe_config()
            cls.after_wipe = sorted(path.name for path in cls.config.iterdir())
            cls.ha.rerender_config()
            cls.ha.start()
            cls.second = cls.ha.seed("seed", "--integration-dir", cls.served_dir)
            cls.after = cls.ha.run_async(cls._admin_call(cls.read_state)) if cls.second.returncode == 0 else None
        except BaseException:
            cls.ha.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ha.__exit__(None, None, None)

    # -- helpers ---------------------------------------------------------------------------------

    @classmethod
    async def _admin_call(cls, fn, *args):
        async with cls.ha.admin_session() as (client, token, ws):
            return await fn(client, token, ws, *args)

    @staticmethod
    async def find_user(_client, _token, ws, name: str) -> str:
        users = (await ws.call("config/auth/list"))["result"]
        return next(u["id"] for u in users if u["name"] == name and not u["system_generated"])

    @staticmethod
    async def read_state(_client, _token, ws) -> dict:
        """What her cards would show: the reward catalog, the balances and every chore's progress."""
        rewards = (await ws.call("family_hub/rewards/get_state"))["result"]
        chores = (await ws.call("family_hub/chores/list"))["result"]["chores"]
        return {
            "catalog": sorted(r["title"] for r in rewards["catalog"]),
            "balances": dict(rewards["balances"]),
            "redemptions": len(rewards.get("redemptions") or []),
            "chores": sorted((c["title"], c["assigned_to"], c["status"], bool(c.get("completed_at"))) for c in chores),
        }

    @classmethod
    async def mutate(cls, _client, _token, ws) -> dict:
        """Create a canary reward and tick one of the child's chores (the ids are kept for the report)."""
        await ws.call("family_hub/rewards/add_catalog_item", title="Canary reward", cost_stars=3)
        chores = (await ws.call("family_hub/chores/list"))["result"]["chores"]
        mine = [c for c in chores if c["assigned_to"] == cls.child_id and c.get("no_approval_required")]
        reply = await ws.call("family_hub/chores/complete", chore_id=mine[0]["id"])
        return {"title": mine[0]["title"], "chore": reply["result"]["chore"]}

    # -- the tests -------------------------------------------------------------------------------

    def test_a_her_earlier_data_existed_before_the_reset(self) -> None:
        self.assertTrue(self.before_wipe["storage"])
        self.assertTrue(self.before_wipe["backups"], "the integration's own backups must exist for the test to mean anything")
        now = self.before_wipe["after_mutation"]
        self.assertIn("Canary reward", now["catalog"])
        self.assertNotEqual(now["chores"], self.fresh["chores"], "a ticked chore must differ from the fresh seed")
        self.assertNotEqual(now["balances"], self.fresh["balances"])

    def test_b_the_wipe_removed_everything_but_the_integration(self) -> None:
        self.assertEqual(self.wipe.returncode, 0, self.wipe.stderr + self.wipe.stdout)
        self.assertEqual(self.after_wipe, ["custom_components"])
        self.assertTrue((self.config / "custom_components" / "family_hub" / "manifest.json").exists())

    def test_c_the_second_seed_succeeded_and_ended_in_verify(self) -> None:
        self.assertEqual(self.second.returncode, 0, self.second.stdout + self.second.stderr)
        self.assertIn("onboarded", self.second.stdout)
        self.assertIn("verify: all", self.second.stdout)

    def test_d_the_canary_reward_and_the_tick_are_gone(self) -> None:
        self.assertIsNotNone(self.after)
        self.assertNotIn("Canary reward", self.after["catalog"])
        self.assertEqual(self.after["redemptions"], 0)
        statuses = {(title, status, done) for title, _who, status, done in self.after["chores"]}
        fresh = {(title, status, done) for title, _who, status, done in self.fresh["chores"]}
        self.assertEqual(statuses, fresh)

    def test_e_catalog_balances_and_chores_equal_a_fresh_seed(self) -> None:
        self.assertEqual(len(self.after["catalog"]), 5)
        self.assertEqual(self.after["catalog"], self.fresh["catalog"])
        for user_id in self.after["balances"]:
            self.assertEqual(self.after["balances"][user_id], 18, user_id)
        self.assertEqual(len(self.after["balances"]), len(self.fresh["balances"]))
        self.assertEqual(
            sorted((title, status) for title, _who, status, _done in self.after["chores"]),
            sorted((title, status) for title, _who, status, _done in self.fresh["chores"]),
        )

    def test_f_her_stored_credentials_still_log_her_in(self) -> None:
        login = self.ha.credentials()["members"][self.HER]

        async def whoami():
            async with HAClient(self.ha.base_url, self.ha.ca) as client:
                token = await client.login(login["username"], login["password"])
                ws = await client.ws(token)
                return (await ws.call("auth/current_user"))["result"]

        me = self.ha.run_async(whoami())
        self.assertEqual(me["name"], self.HER)
        self.assertFalse(me["is_admin"])


if __name__ == "__main__":
    unittest.main()
