"""verify's pure checks: each one names what is wrong, and unreadable input never reads as safe."""
from __future__ import annotations

import copy
import unittest

from tools.seed import verify
from tools.seed.dashboard import DASHBOARD_VIEWS, build_config
from tools.seed.envs import ENVIRONMENTS
from tools.seed.family_file import EXAMPLE_FILE, load

DEV = ENVIRONMENTS["dev"]
PREVIEW = ENVIRONMENTS["preview"]
FALSE_FLAGS = ("remindersEnabled", "digestEnabled", "notifyRewardClaimed", "notifyChoreApproved", "notifyTimerAlarm")


def profile(targets: object = None, **flags: bool) -> dict:
    base = {"notifyTargets": [] if targets is None else targets}
    base.update({flag: False for flag in FALSE_FLAGS})
    base.update(flags)
    return base


def safe_settings() -> dict:
    return {
        "userProfiles": {"u-b": profile(["notify.persistent_notification"]), "u-a": profile([])},
        "alarmDevices": [],
    }


class IdentityTests(unittest.TestCase):
    def test_exact_name_theme_and_title_pass(self) -> None:
        self.assertEqual(verify.check_identity("Family Hub DEV", DEV, "blossom", "Family Hub DEV"), [])
        self.assertEqual(verify.check_identity("Family Hub PREVIEW", PREVIEW, "midnight", "Family Hub PREVIEW"), [])

    def test_empty_location_name_fails(self) -> None:
        failures = verify.check_identity("", DEV, "blossom", "Family Hub DEV")
        self.assertTrue(any("location_name" in f for f in failures), failures)

    def test_trailing_space_fails(self) -> None:
        failures = verify.check_identity("Family Hub DEV ", DEV, "blossom", "Family Hub DEV")
        self.assertTrue(any("location_name" in f for f in failures), failures)

    def test_other_environments_name_fails(self) -> None:
        failures = verify.check_identity("Family Hub PREVIEW", DEV, "blossom", "Family Hub DEV")
        self.assertTrue(any("location_name" in f for f in failures), failures)

    def test_missing_or_wrong_theme_fails(self) -> None:
        for theme in (None, "", "slate", "midnight"):
            failures = verify.check_identity("Family Hub DEV", DEV, theme, "Family Hub DEV")
            self.assertTrue(any("globalThemeId" in f for f in failures), (theme, failures))

    def test_wrong_dashboard_title_fails(self) -> None:
        failures = verify.check_identity("Family Hub DEV", DEV, "blossom", "Family Hub")
        self.assertTrue(any("dashboard title" in f for f in failures), failures)


class IsolationTests(unittest.TestCase):
    def run_check(self, settings=None, entities=(), domains=("family_hub", "local_todo"), components=("frontend",)):
        return verify.check_isolation(
            safe_settings() if settings is None else settings, list(entities), list(domains), list(components)
        )

    def test_empty_and_persistent_notification_targets_pass(self) -> None:
        self.assertEqual(self.run_check(), [])

    def test_lookalike_and_real_phone_targets_fail_as_whole_strings(self) -> None:
        for target in ("notify.persistent_notification_x", "notify.mobile_app_pixel", "notify.persistent"):
            settings = safe_settings()
            settings["userProfiles"]["u-a"] = profile([target])
            failures = self.run_check(settings)
            self.assertTrue(any("notifyTargets" in f and "u-a" in f and target in f for f in failures), (target, failures))

    def test_unreadable_settings_fail_and_are_never_safe(self) -> None:
        for settings in (None, [], "x", {"userProfiles": []}, {"userProfiles": None}, {}):
            failures = verify.check_isolation(settings, [], ["family_hub"], ["frontend"])
            self.assertTrue(any("settings unreadable" in f for f in failures), (settings, failures))

    def test_a_profile_that_is_not_a_mapping_fails(self) -> None:
        settings = safe_settings()
        settings["userProfiles"]["u-a"] = "oops"
        self.assertTrue(any("settings unreadable" in f for f in self.run_check(settings)))

    def test_targets_that_are_not_a_list_fail(self) -> None:
        settings = safe_settings()
        settings["userProfiles"]["u-a"]["notifyTargets"] = "notify.persistent_notification"
        self.assertTrue(any("notifyTargets" in f for f in self.run_check(settings)))

    def test_offenders_are_reported_sorted_by_user_id_and_any_one_fails(self) -> None:
        settings = safe_settings()
        settings["userProfiles"]["u-z"] = profile(["notify.mobile_app_z"])
        settings["userProfiles"]["u-c"] = profile(["notify.mobile_app_c", "notify.mobile_app_a"])
        failures = [f for f in self.run_check(settings) if "notifyTargets" in f]
        self.assertEqual(len(failures), 3)
        order = [next(u for u in ("u-c", "u-z") if u in f) for f in failures]
        self.assertEqual(order, ["u-c", "u-c", "u-z"])
        self.assertIn("notify.mobile_app_a", failures[0])  # targets are sorted within a user
        self.assertIn("notify.mobile_app_c", failures[1])
        self.assertIn("notify.mobile_app_z", failures[2])

    def test_notification_flags_must_be_off(self) -> None:
        for flag in FALSE_FLAGS:
            settings = safe_settings()
            settings["userProfiles"]["u-a"][flag] = True
            failures = self.run_check(settings)
            self.assertTrue(any(flag in f and "u-a" in f for f in failures), (flag, failures))

    def test_non_empty_alarm_devices_fail(self) -> None:
        settings = safe_settings()
        settings["alarmDevices"] = [{"entity_id": "media_player.kitchen"}]
        self.assertTrue(any("alarmDevices" in f for f in self.run_check(settings)))

    def test_media_player_and_assist_satellite_entities_fail(self) -> None:
        self.assertTrue(any("media_player.kitchen" in f for f in self.run_check(entities=["media_player.kitchen"])))
        self.assertTrue(any("assist_satellite.x" in f for f in self.run_check(entities=["assist_satellite.x"])))
        self.assertEqual(self.run_check(entities=["media_player_extra.x", "todo.groceries"]), [])

    def test_entry_domains_outside_the_allow_list_fail(self) -> None:
        failures = self.run_check(domains=["family_hub", "radio_browser"])
        self.assertTrue(any("radio_browser" in f for f in failures), failures)
        for domain in verify.ALLOWED_ENTRY_DOMAINS:
            self.assertEqual(self.run_check(domains=[domain]), [], domain)

    def test_forbidden_components_fail(self) -> None:
        failures = self.run_check(components=["frontend", "zeroconf"])
        self.assertTrue(any("zeroconf" in f for f in failures), failures)
        self.assertEqual(self.run_check(components=["frontend", "zeroconf_extra", "sensor.sun"]), [])


class GrocyTests(unittest.TestCase):
    def test_not_configured_passes(self) -> None:
        self.assertEqual(verify.check_grocy({"configured": False, "recipes": []}), [])

    def test_configured_or_unreadable_fails(self) -> None:
        for reply in ({"configured": True}, None, [], {"recipes": []}, {"configured": "no"}):
            self.assertTrue(verify.check_grocy(reply), reply)


class DashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.family = load(str(EXAMPLE_FILE), lambda _line: None)
        self.calendars = {m.first_name: "calendar.%s" % m.first_name.lower() for m in self.family.members}
        self.config = build_config(DEV, self.family, self.calendars)
        self.entry = {
            "url_path": "family-hub",
            "require_admin": False,
            "title": "Family Hub DEV",
            "icon": "mdi:home-heart",
            "show_in_sidebar": True,
        }

    def test_the_dashboard_the_seed_builds_passes(self) -> None:
        self.assertEqual(verify.check_dashboard(self.entry, self.config, DEV), [])

    def test_missing_dashboard_fails(self) -> None:
        self.assertTrue(verify.check_dashboard(None, None, DEV))

    def test_admin_only_dashboard_fails(self) -> None:
        self.entry["require_admin"] = True
        self.assertTrue(any("require_admin" in f for f in verify.check_dashboard(self.entry, self.config, DEV)))

    def test_wrong_view_order_fails(self) -> None:
        self.config["views"].reverse()
        self.assertTrue(verify.check_dashboard(self.entry, self.config, DEV))

    def test_view_without_icon_or_with_two_cards_fails(self) -> None:
        config = copy.deepcopy(self.config)
        del config["views"][2]["icon"]
        self.assertTrue(any("icon" in f for f in verify.check_dashboard(self.entry, config, DEV)))
        config = copy.deepcopy(self.config)
        config["views"][0]["cards"].append({"type": "custom:family-today-card"})
        self.assertTrue(any("card" in f for f in verify.check_dashboard(self.entry, config, DEV)))

    def test_every_view_is_expected(self) -> None:
        self.assertEqual(len(self.config["views"]), len(DASHBOARD_VIEWS))


class SidebarTests(unittest.TestCase):
    PANELS = ["lovelace", "profile", "notfound", "family-hub", "theme-builder", "map"]

    def good(self) -> tuple[dict, dict]:
        return (
            {"panelOrder": [], "hiddenPanels": ["lovelace", "map", "theme-builder"]},
            {"default_panel": "family-hub"},
        )

    def test_exact_sidebar_passes(self) -> None:
        sidebar, core = self.good()
        self.assertEqual(verify.check_sidebar("Her", self.PANELS, sidebar, core), [])

    def test_unsorted_or_missing_hidden_panel_fails(self) -> None:
        sidebar, core = self.good()
        sidebar["hiddenPanels"] = ["map", "lovelace", "theme-builder"]
        self.assertTrue(verify.check_sidebar("Her", self.PANELS, sidebar, core))
        sidebar["hiddenPanels"] = ["lovelace", "map"]
        self.assertTrue(verify.check_sidebar("Her", self.PANELS, sidebar, core))

    def test_lookalike_panel_must_be_hidden(self) -> None:
        panels = self.PANELS + ["family-hub-x"]
        sidebar, core = self.good()
        self.assertTrue(verify.check_sidebar("Her", panels, sidebar, core))
        sidebar["hiddenPanels"] = sorted(sidebar["hiddenPanels"] + ["family-hub-x"])
        self.assertEqual(verify.check_sidebar("Her", panels, sidebar, core), [])

    def test_missing_family_hub_panel_fails(self) -> None:
        sidebar, core = self.good()
        failures = verify.check_sidebar("Her", [p for p in self.PANELS if p != "family-hub"], sidebar, core)
        self.assertTrue(any("family-hub" in f for f in failures), failures)

    def test_only_panel_means_nothing_hidden(self) -> None:
        self.assertEqual(
            verify.check_sidebar("Her", ["family-hub"], {"panelOrder": [], "hiddenPanels": []}, {"default_panel": "family-hub"}),
            [],
        )

    def test_unreadable_sidebar_or_wrong_default_fails(self) -> None:
        _sidebar, core = self.good()
        self.assertTrue(verify.check_sidebar("Her", self.PANELS, None, core))
        sidebar, _core = self.good()
        self.assertTrue(verify.check_sidebar("Her", self.PANELS, sidebar, {"default_panel": "lovelace"}))
        self.assertTrue(verify.check_sidebar("Her", self.PANELS, sidebar, None))


class ContentTests(unittest.TestCase):
    def counts(self) -> dict:
        return {
            "children": ["Riley", "Casey"],
            "chores": {"Riley": 5, "Casey": 4},
            "rewards": 5,
            "goals": 1,
            "routines": 6,
            "recipes": 3,
            "pantry": 3,
            "meals": 6,
            "groceries": 6,
            "errands": 3,
            "suggestions": 1,
        }

    def test_seeded_counts_pass(self) -> None:
        self.assertEqual(verify.check_content(self.counts()), [])

    def test_any_empty_list_or_catalog_fails_and_is_named(self) -> None:
        for key in ("rewards", "goals", "routines", "recipes", "pantry", "meals", "groceries", "errands", "suggestions"):
            counts = self.counts()
            counts[key] = 0
            failures = verify.check_content(counts)
            self.assertTrue(any(key in f and "empty" in f for f in failures), (key, failures))

    def test_a_child_with_too_few_chores_fails(self) -> None:
        counts = self.counts()
        counts["chores"]["Casey"] = 0
        self.assertTrue(any("Casey" in f for f in verify.check_content(counts)))

    def test_a_family_without_children_needs_no_chores_or_rewards(self) -> None:
        counts = self.counts()
        counts.update({"children": [], "chores": {}, "rewards": 0, "goals": 0, "routines": 0})
        self.assertEqual(verify.check_content(counts), [])


if __name__ == "__main__":
    unittest.main()
