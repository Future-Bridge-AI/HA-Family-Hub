"""Live test: the full seed with the example family on a real Home Assistant 2026.10.4.

One HA boot and one ``seed`` run for the whole class; the tests read the result back the way the
family's cards and her login would. Port 18131 belongs to this module.

Run: FH_HASS=$HOME/.cache/fh-hassfest/venv/bin/hass python -B -m unittest discover \
        -s tools/seed/tests -t . -p 'live_family.py' -v
"""
from __future__ import annotations

import subprocess
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from tools.seed.client import HAClient
from tools.seed.dashboard import DASHBOARD_VIEWS, KEEP_PANELS

from .live_ha import HOST_ENV, LiveHA

# The invented example family (tools/seed/data/family.example.yaml).
ADMIN_PARENT = "Sam"
HER = "Jordan"
CHILDREN = ("Riley", "Casey")
EVERYONE = (ADMIN_PARENT, HER, *CHILDREN)
TODO_ENTITIES = (
    "todo.recipe_box",
    "todo.meal_plan",
    "todo.meal_plan_templates",
    "todo.meal_suggestions",
    "todo.family_reminders",
    "todo.groceries",
    "todo.errands",
)


class LiveFamilyTests(unittest.TestCase):
    ha: LiveHA
    first: subprocess.CompletedProcess

    @classmethod
    def setUpClass(cls) -> None:
        cls.ha = LiveHA("dev", 18131)
        cls.ha.__enter__()
        try:
            cls.first = cls.ha.seed("seed")
        except BaseException:
            cls.ha.__exit__(None, None, None)
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.ha.__exit__(None, None, None)

    # -- helpers ---------------------------------------------------------------------------------

    def read_admin(self, coro_fn):
        """Run ``coro_fn(client, token, ws)`` as the tooling admin and return its result."""

        async def run():
            async with self.ha.admin_session() as (client, token, ws):
                return await coro_fn(client, token, ws)

        return self.ha.run_async(run())

    def as_member(self, first_name: str, coro_fn):
        """Run ``coro_fn(ws)`` logged in as a family member with the stored password."""
        login = self.ha.credentials()["members"][first_name]

        async def run():
            async with HAClient(self.ha.base_url, self.ha.ca) as client:
                token = await client.login(login["username"], login["password"])
                ws = await client.ws(token)
                return await coro_fn(ws)

        return self.ha.run_async(run())

    def users(self) -> dict[str, dict]:
        async def read(_client, _token, ws):
            return (await ws.call("config/auth/list"))["result"]

        return {u["name"]: u for u in self.read_admin(read) if not u["system_generated"]}

    def child_ids(self) -> dict[str, str]:
        users = self.users()
        return {name: users[name]["id"] for name in CHILDREN}

    def snapshot(self) -> dict:
        """What the cards would read back, as counts and sets (used to prove a re-seed adds nothing)."""

        async def read(_client, _token, ws):
            async def items(entity):
                reply = await ws.call(
                    "call_service",
                    domain="todo",
                    service="get_items",
                    service_data={"entity_id": entity, "status": ["needs_action", "completed"]},
                    return_response=True,
                )
                return reply["result"]["response"][entity]["items"]

            rewards = (await ws.call("family_hub/rewards/get_state"))["result"]
            return {
                "chores": sorted(
                    (c["title"], c["assigned_to"]) for c in (await ws.call("family_hub/chores/list"))["result"]["chores"]
                ),
                "catalog": sorted(r["title"] for r in rewards["catalog"]),
                "balances": rewards["balances"],
                "goals": len((await ws.call("family_hub/goals/list"))["result"]["goals"]),
                "routines": len((await ws.call("family_hub/routines/list"))["result"]["items"]),
                "pantry": len((await ws.call("family_hub/pantry_extras/list"))["result"]["extras"]),
                "recipes": len((await ws.call("family_hub/get_recipes"))["result"]["recipes"]),
                "meals": sorted(i["due"] for i in await items("todo.meal_plan")),
                "groceries": len(await items("todo.groceries")),
                "errands": len(await items("todo.errands")),
                "suggestions": len(await items("todo.meal_suggestions")),
            }

        return self.read_admin(read)

    # -- task 1: her login lands on the Family Hub dashboard --------------------------------------

    def test_a_seed_exits_zero_and_reports_each_step(self) -> None:
        self.assertEqual(self.first.returncode, 0, self.first.stderr + self.first.stdout)
        for line in ("users:", "to-do lists:", "calendars:", "family hub:", "dashboard:", "sidebar:"):
            self.assertIn(line, self.first.stdout)

    def test_b_every_member_has_an_account_in_the_right_group(self) -> None:
        users = self.users()
        self.assertEqual(users[ADMIN_PARENT]["group_ids"], ["system-admin"])
        for name in (HER, *CHILDREN):
            self.assertEqual(users[name]["group_ids"], ["system-users"], name)
        self.assertIn("Family Hub tools", users)
        self.assertEqual(users["Family Hub tools"]["username"], "fhtools")
        self.assertEqual(len(users), 5)

    def test_c_her_login_is_not_admin_and_sees_only_family_hub(self) -> None:
        async def read(ws):
            me = (await ws.call("auth/current_user"))["result"]
            panels = (await ws.call("get_panels"))["result"]
            sidebar = (await ws.call("frontend/get_user_data", key="sidebar"))["result"]["value"]
            core = (await ws.call("frontend/get_user_data", key="core"))["result"]["value"]
            return me, panels, sidebar, core

        me, panels, sidebar, core = self.as_member(HER, read)
        self.assertFalse(me["is_admin"])
        self.assertIn("family-hub", panels)
        self.assertEqual(sidebar["panelOrder"], [])
        self.assertEqual(sidebar["hiddenPanels"], sorted(p for p in panels if p not in KEEP_PANELS))
        self.assertNotIn("family-hub", sidebar["hiddenPanels"])
        self.assertEqual(core["default_panel"], "family-hub")

    def test_d_lists_and_calendars_exist(self) -> None:
        async def read(_client, _token, ws):
            return (await ws.call("get_states"))["result"]

        states = {s["entity_id"]: s for s in self.read_admin(read)}
        for entity in TODO_ENTITIES:
            self.assertIn(entity, states)
        calendars = {
            s["attributes"].get("friendly_name") for e, s in states.items() if e.startswith("calendar.")
        }
        self.assertEqual(calendars, set(EVERYONE))

    def test_e_family_hub_entry_is_loaded(self) -> None:
        async def read(client, token, _ws):
            return (await client.rest("GET", "/api/config/config_entries/entry?domain=family_hub", token=token))[1]

        entries = self.read_admin(read)
        self.assertEqual([e["state"] for e in entries], ["loaded"])

    def test_f_dashboard_has_one_card_per_tab(self) -> None:
        async def read(_client, _token, ws):
            listed = (await ws.call("lovelace/dashboards/list"))["result"]
            config = (await ws.call("lovelace/config", url_path="family-hub"))["result"]
            return listed, config

        listed, config = self.read_admin(read)
        mine = [d for d in listed if d["url_path"] == "family-hub"]
        self.assertEqual(len(mine), 1)
        self.assertFalse(mine[0]["require_admin"])
        self.assertEqual(mine[0]["title"], "Family Hub DEV")
        self.assertEqual(mine[0]["icon"], "mdi:home-heart")
        views = config["views"]
        self.assertEqual(
            [v["title"] for v in views], ["Calendar", "Today", "Chores", "Rewards", "To-dos", "Recipes", "Pantry"]
        )
        self.assertEqual([v["title"] for v in views], [t for t, _p, _i, _c in DASHBOARD_VIEWS])
        for view in views:
            self.assertEqual(view["type"], "panel")
            self.assertTrue(view["icon"].startswith("mdi:"), view)
            self.assertEqual(len(view["cards"]), 1)

    # -- task 2: her pretend week ------------------------------------------------------------------

    def test_g_each_child_has_recurring_chores_two_of_them_due_today(self) -> None:
        zone = ZoneInfo(HOST_ENV["TZ"])
        today = datetime.now(zone).date()

        async def read(_client, _token, ws):
            return (await ws.call("family_hub/chores/list"))["result"]["chores"]

        chores = self.read_admin(read)
        for name, user_id in self.child_ids().items():
            mine = [c for c in chores if c["assigned_to"] == user_id]
            self.assertTrue(4 <= len(mine) <= 6, "%s has %d chores" % (name, len(mine)))
            due = [datetime.fromisoformat(c["due_date"]).astimezone(zone).date() for c in mine]
            self.assertGreaterEqual(sum(1 for d in due if d == today), 2, name)
            self.assertTrue(all(d >= today for d in due), "an overdue chore for %s" % name)
            for chore in mine:
                self.assertTrue(chore["recur_type"] in ("interval", "weekdays"), chore)
                self.assertEqual(chore["reminder_minutes"], [])
                self.assertTrue(chore["no_approval_required"])

    def test_h_rewards_and_balances(self) -> None:
        snap = self.snapshot()
        self.assertEqual(len(snap["catalog"]), 5)
        for user_id in self.child_ids().values():
            self.assertEqual(snap["balances"].get(user_id), 18)

    def test_i_dinners_on_six_of_the_next_seven_nights(self) -> None:
        today = datetime.now(ZoneInfo(HOST_ENV["TZ"])).date()
        window = {(today + timedelta(days=n)).isoformat() for n in range(7)}
        dues = [d[:10] for d in self.snapshot()["meals"]]
        self.assertEqual(len(dues), 6)
        self.assertTrue(set(dues) <= window)

    def test_j_lists_recipes_pantry_goal_and_routine(self) -> None:
        snap = self.snapshot()
        self.assertEqual((snap["groceries"], snap["errands"], snap["suggestions"]), (6, 3, 1))
        self.assertEqual(snap["recipes"], 3)
        self.assertEqual(snap["pantry"], 3)
        self.assertEqual(snap["goals"], 1)
        self.assertEqual(snap["routines"], 6)

    def test_k_theme_and_kid_sign_in(self) -> None:
        async def read(_client, _token, ws):
            return (await ws.call("family_hub/get_settings"))["result"]["settings"]

        settings = self.read_admin(read)
        self.assertEqual(settings["globalThemeId"], "blossom")
        self.assertTrue(settings["useGlobalTheme"])
        self.assertTrue(set(self.child_ids().values()) <= set(settings["kioskLoginEnabledUserIds"]))

    def test_y_kid_pin_signs_in_through_kiosk_elevate(self) -> None:
        creds = self.ha.credentials()["members"]
        users = self.users()

        async def elevate(ws):
            outcome = {}
            for name in CHILDREN:
                reply = await ws.call("family_hub/kiosk/elevate", user_id=users[name]["id"], pin=creds[name]["pin"])
                outcome[name] = reply["result"]["user_id"]
            return outcome

        outcome = self.as_member(HER, elevate)
        self.assertEqual(outcome, {name: users[name]["id"] for name in CHILDREN})

    def test_z_second_seed_changes_nothing(self) -> None:
        before = {name: u["id"] for name, u in self.users().items()}
        content_before = self.snapshot()
        second = self.ha.seed("seed")
        self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
        self.assertEqual({name: u["id"] for name, u in self.users().items()}, before)
        self.assertEqual(self.snapshot(), content_before)

        async def read(client, token, ws):
            entries = (await client.rest("GET", "/api/config/config_entries/entry", token=token))[1]
            dashboards = (await ws.call("lovelace/dashboards/list"))["result"]
            registry = (await ws.call("config/entity_registry/list"))["result"]
            return entries, dashboards, registry

        entries, dashboards, registry = self.read_admin(read)
        self.assertEqual(len([e for e in entries if e["domain"] == "family_hub"]), 1)
        self.assertEqual(len([d for d in dashboards if d["url_path"] == "family-hub"]), 1)
        todo_ids = [r["entity_id"] for r in registry if r["entity_id"].startswith("todo.")]
        self.assertEqual(sorted(todo_ids), sorted(set(todo_ids)))
        for entity in TODO_ENTITIES:
            self.assertEqual(todo_ids.count(entity), 1, entity)


if __name__ == "__main__":
    unittest.main()
