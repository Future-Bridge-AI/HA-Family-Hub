"""verify: fail loudly if anything could reach a real phone, or anything she relies on is missing.

The ``check_*`` functions are pure: each takes what was read from Home Assistant and returns a
list of problems (empty means the check passed). Unreadable input is always a problem and never
reads as "nothing to worry about". ``run_verify`` reads everything from a live instance, runs the
checks in a stable order and prints one ``FAIL <check>: <detail>`` line per problem.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Iterable, Optional

from . import family_hub as family_hub_mod
from . import resources as resources_mod
from .client import HAClient, HAWebSocket, SeedError
from .creds import CredentialStore
from .dashboard import DASHBOARD_ICON, DASHBOARD_URL_PATH, DASHBOARD_VIEWS, KEEP_PANELS
from .entries import list_entries
from .envs import Env
from .family_file import Family

_LOGGER = logging.getLogger(__name__)

# Notification targets a profile may keep: HA's own in-app notification, nothing else (whole-string match).
ALLOWED_NOTIFY_TARGETS = ("notify.persistent_notification",)
NOTIFICATION_FLAGS = (
    "remindersEnabled",
    "digestEnabled",
    "notifyRewardClaimed",
    "notifyChoreApproved",
    "notifyTimerAlarm",
)
ALLOWED_ENTRY_DOMAINS = (
    "family_hub",
    "local_calendar",
    "local_todo",
    "google",
    "mobile_app",
    "analytics",
    "backup",
    "sun",
    "shopping_list",
)
FORBIDDEN_COMPONENTS = (
    "zeroconf",
    "ssdp",
    "dhcp",
    "bluetooth",
    "usb",
    "cloud",
    "homeassistant_alerts",
    "default_config",
)
FORBIDDEN_ENTITY_DOMAINS = ("media_player", "assist_satellite")

# What a seeded instance holds at least, per area. They do not decay with the calendar (a chore
# recurs, a list item stays), so a later standalone verify does not raise a false alarm.
MINIMUM_PER_CHILD_CHORES = 4
MINIMUM_COUNTS: dict[str, int] = {
    "meals": 1,  # dinners dated today or later: the nights pass, so only "not empty"
    "groceries": 6,
    "errands": 3,
    "suggestions": 1,
    "recipes": 3,
    "pantry": 3,
}
MINIMUM_COUNTS_WITH_CHILDREN: dict[str, int] = {"rewards": 5, "goals": 1}
MINIMUM_ROUTINE_STEPS_PER_CHILD = 3


# -- pure checks ---------------------------------------------------------------------------------


def check_identity(location_name: Any, env: Env, theme_id: Any, dashboard_title: Any) -> list[str]:
    """The location name, global theme and dashboard title all name the environment, exactly."""
    problems = []
    if location_name != env.location_name:
        problems.append("location_name is %r, expected %r" % (location_name, env.location_name))
    if theme_id != env.theme:
        problems.append("globalThemeId is %r, expected %r" % (theme_id, env.theme))
    if dashboard_title != env.dashboard_title:
        problems.append("dashboard title is %r, expected %r" % (dashboard_title, env.dashboard_title))
    return problems


def check_isolation(settings: Any, entities: Iterable[str], entry_domains: Iterable[str], components: Iterable[str]) -> list[str]:
    """Nothing here can notify a real phone or ring a speaker (PREV-03)."""
    problems: list[str] = []
    profiles: dict = {}
    if isinstance(settings, dict) and isinstance(settings.get("userProfiles"), dict):
        profiles = settings["userProfiles"]
    else:
        problems.append("settings unreadable: no userProfiles mapping (%s)" % type(settings).__name__)

    for user_id in sorted(profiles):
        profile = profiles[user_id]
        if not isinstance(profile, dict):
            problems.append("settings unreadable: the profile of user %s is not a mapping" % user_id)
            continue
        targets = profile.get("notifyTargets")
        if not isinstance(targets, list):
            problems.append("notifyTargets of user %s is not a list: %r" % (user_id, targets))
            continue
        for target in sorted(str(t) for t in targets):
            if target not in ALLOWED_NOTIFY_TARGETS:
                problems.append("notifyTargets of user %s includes %r" % (user_id, target))
        for flag in NOTIFICATION_FLAGS:
            if profile.get(flag):
                problems.append("%s is on for user %s" % (flag, user_id))

    if isinstance(settings, dict) and settings.get("alarmDevices"):
        problems.append("alarmDevices is not empty: %r" % (settings.get("alarmDevices"),))

    for entity in sorted(str(e) for e in entities):
        if entity.split(".", 1)[0] in FORBIDDEN_ENTITY_DOMAINS:
            problems.append("entity %s exists (speakers and satellites are not allowed)" % entity)
    for domain in sorted({str(d) for d in entry_domains}):
        if domain not in ALLOWED_ENTRY_DOMAINS:
            problems.append("config entry domain %r is not allowed" % domain)
    loaded = {str(c) for c in components}
    for component in FORBIDDEN_COMPONENTS:
        if component in loaded:
            problems.append("component %s is loaded" % component)
    return problems


def check_grocy(reply: Any) -> list[str]:
    """Grocy URL and key are blank (the instance may not call out to a real Grocy)."""
    if not isinstance(reply, dict) or not isinstance(reply.get("configured"), bool):
        return ["Grocy status unreadable: %r" % (reply,)]
    if reply["configured"]:
        return ["Grocy is configured (URL and key must be blank)"]
    return []


def check_dashboard(entry: Any, config: Any, env: Env) -> list[str]:
    """Her dashboard exists, is open to non-admins and has one card per tab, each tab with an icon."""
    if not isinstance(entry, dict):
        return ["dashboard %s is missing" % DASHBOARD_URL_PATH]
    problems = []
    if entry.get("require_admin") is not False:
        problems.append("dashboard require_admin is %r, expected False" % (entry.get("require_admin"),))
    if entry.get("title") != env.dashboard_title:
        problems.append("dashboard title is %r, expected %r" % (entry.get("title"), env.dashboard_title))
    if entry.get("icon") != DASHBOARD_ICON:
        problems.append("dashboard icon is %r, expected %r" % (entry.get("icon"), DASHBOARD_ICON))
    if entry.get("show_in_sidebar") is not True:
        problems.append("dashboard is not shown in the sidebar")
    views = config.get("views") if isinstance(config, dict) else None
    if not isinstance(views, list):
        problems.append("dashboard config unreadable: no views list")
        return problems
    expected_titles = [title for title, _path, _icon, _card in DASHBOARD_VIEWS]
    actual_titles = [v.get("title") if isinstance(v, dict) else None for v in views]
    if actual_titles != expected_titles:
        problems.append("dashboard views are %s, expected %s" % (actual_titles, expected_titles))
        return problems
    for view, (title, path, _icon, card) in zip(views, DASHBOARD_VIEWS):
        if view.get("type") != "panel":
            problems.append("view %s is type %r, expected panel" % (title, view.get("type")))
        if view.get("path") != path:
            problems.append("view %s has path %r, expected %r" % (title, view.get("path"), path))
        icon = view.get("icon")
        if not (isinstance(icon, str) and icon.startswith("mdi:")):
            problems.append("view %s has no mdi icon (%r)" % (title, icon))
        cards = view.get("cards")
        if not isinstance(cards, list) or len(cards) != 1:
            problems.append("view %s has %s cards, expected exactly one card" % (title, len(cards) if isinstance(cards, list) else "no"))
        elif cards[0].get("type") != card["type"]:
            problems.append("view %s card is %r, expected %r" % (title, cards[0].get("type"), card["type"]))
    return problems


def check_sidebar(member: str, panels: Any, sidebar: Any, core: Any) -> list[str]:
    """A member sees only Family Hub (and profile, notfound): everything else hidden, Family Hub the default."""
    ids = list(panels) if panels is not None else []
    if "family-hub" not in ids:
        return ["%s: the family-hub panel is not in their panel list" % member]
    problems = []
    expected = sorted(p for p in ids if p not in KEEP_PANELS)
    if not isinstance(sidebar, dict) or not isinstance(sidebar.get("hiddenPanels"), list):
        problems.append("%s: sidebar data unreadable: %r" % (member, sidebar))
    else:
        if sidebar["hiddenPanels"] != expected:
            problems.append("%s: hiddenPanels is %s, expected %s" % (member, sidebar["hiddenPanels"], expected))
        if sidebar.get("panelOrder") != []:
            problems.append("%s: panelOrder is %r, expected []" % (member, sidebar.get("panelOrder")))
    default = core.get("default_panel") if isinstance(core, dict) else core
    if default != "family-hub":
        problems.append("%s: default_panel is %r, expected family-hub" % (member, default))
    return problems


def check_content(counts: Any) -> list[str]:
    """No seeded list or catalog reads back empty, and each holds at least what was seeded."""
    if not isinstance(counts, dict):
        return ["content counts unreadable"]
    problems = []
    children = list(counts.get("children") or [])
    minimums = dict(MINIMUM_COUNTS)
    if children:
        minimums.update(MINIMUM_COUNTS_WITH_CHILDREN)
        minimums["routines"] = MINIMUM_ROUTINE_STEPS_PER_CHILD * len(children)
    for key in sorted(minimums):
        found = int(counts.get(key) or 0)
        if found == 0:
            problems.append("%s is empty" % key)
        elif found < minimums[key]:
            problems.append("%s has %d, needs at least %d" % (key, found, minimums[key]))
    per_child = counts.get("chores") or {}
    for child in sorted(children):
        found = int(per_child.get(child) or 0)
        if found == 0:
            problems.append("chores for %s is empty" % child)
        elif found < MINIMUM_PER_CHILD_CHORES:
            problems.append("chores for %s has %d, needs at least %d" % (child, found, MINIMUM_PER_CHILD_CHORES))
    return problems


def check_resources(resources: list[dict], files: dict[str, str], urls: dict[str, str]) -> list[str]:
    """Every card's lovelace resource points at the file being served (resources-sync would change nothing)."""
    problems = []
    for action in resources_mod.plan_updates(resources, files, urls):
        if action["action"] == "update":
            problems.append("resource %s is stale (%s)" % (action["resource_id"], action["old_url"]))
        elif action["action"] == "create":
            problems.append("no resource for %s" % action["url"].split("?", 1)[0])
        else:
            problems.append("duplicate resources for %s" % action["file"])
    return problems


# -- gathering from a live instance -------------------------------------------------------------


async def _read_settings(ws: HAWebSocket) -> Optional[dict]:
    try:
        return await family_hub_mod.get_settings(ws)
    except SeedError as err:
        _LOGGER.debug("settings unreadable: %s", err)
        return None


async def _gather_counts(ws: HAWebSocket, family: Family, users_by_login: dict[str, str], today: Any) -> dict:
    chores = (await ws.call("family_hub/chores/list"))["result"].get("chores") or []
    per_child: dict[str, int] = {}
    for child in family.children:
        user_id = users_by_login.get(child.username)
        per_child[child.first_name] = sum(1 for c in chores if user_id and c.get("assigned_to") == user_id)

    async def count(entity: str) -> int:
        return len(await family_hub_mod.todo_items(ws, entity))

    meals = [
        i
        for i in await family_hub_mod.todo_items(ws, family_hub_mod.MEAL_PLAN_ENTITY)
        if str(i.get("due") or "")[:10] >= today.isoformat()
    ]
    return {
        "children": [c.first_name for c in family.children],
        "chores": per_child,
        "rewards": len((await ws.call("family_hub/rewards/get_state"))["result"].get("catalog") or []),
        "goals": len((await ws.call("family_hub/goals/list"))["result"].get("goals") or []),
        "routines": len((await ws.call("family_hub/routines/list"))["result"].get("items") or []),
        "recipes": len((await ws.call("family_hub/get_recipes"))["result"].get("recipes") or []),
        "pantry": len((await ws.call("family_hub/pantry_extras/list"))["result"].get("extras") or []),
        "meals": len(meals),
        "groceries": await count("todo.groceries"),
        "errands": await count("todo.errands"),
        "suggestions": await count("todo.meal_suggestions"),
    }


async def _member_sidebar(client: HAClient, creds: CredentialStore, member: Any) -> list[str]:
    login = creds.member(member.first_name)
    try:
        token = await client.login(login["username"], login["password"])
        ws = await client.ws(token)
        panels = (await ws.call("get_panels"))["result"]
        sidebar = (await ws.call("frontend/get_user_data", key="sidebar"))["result"].get("value")
        core = (await ws.call("frontend/get_user_data", key="core"))["result"].get("value")
        await ws.close()
    except SeedError as err:
        return ["%s: could not read their sidebar: %s" % (member.first_name, err.message)]
    return check_sidebar(member.first_name, panels, sidebar, core)


async def run_verify(
    client: HAClient,
    token: str,
    ws: HAWebSocket,
    env: Env,
    family: Family,
    creds: CredentialStore,
    integration_dir: str,
    say: Callable[[str], None] = print,
) -> list[str]:
    """Run every check; print one line per problem and a summary. Returns the problem lines."""
    results: list[tuple[str, list[str]]] = []

    config = (await ws.call("get_config"))["result"]
    settings = await _read_settings(ws)
    dashboards = (await ws.call("lovelace/dashboards/list"))["result"]
    entry = next((d for d in dashboards if d.get("url_path") == DASHBOARD_URL_PATH), None)
    dash_config: Any = None
    if entry is not None:
        try:
            dash_config = (await ws.call("lovelace/config", url_path=DASHBOARD_URL_PATH))["result"]
        except SeedError as err:
            _LOGGER.debug("dashboard config unreadable: %s", err)
    theme = settings.get("globalThemeId") if isinstance(settings, dict) else None
    results.append(
        ("identity", check_identity(config.get("location_name"), env, theme, entry.get("title") if entry else None))
    )

    states = (await ws.call("get_states"))["result"]
    entries = await list_entries(client, token)
    results.append(
        (
            "isolation",
            check_isolation(
                settings,
                [s["entity_id"] for s in states],
                [e.get("domain") for e in entries],
                config.get("components") or [],
            ),
        )
    )
    try:
        grocy = (await ws.call("family_hub/get_grocy_recipes"))["result"]
    except SeedError:
        grocy = None
    results.append(("grocy", check_grocy(grocy)))
    results.append(("dashboard", check_dashboard(entry, dash_config, env)))

    for member in family.members:
        if not member.admin:
            results.append(("sidebar", await _member_sidebar(client, creds, member)))

    users = (await ws.call("config/auth/list"))["result"]
    users_by_login = {u.get("username"): u["id"] for u in users if u.get("username")}
    today, _zone = await family_hub_mod.instance_today(ws)
    try:
        counts: Any = await _gather_counts(ws, family, users_by_login, today)
    except SeedError as err:
        counts = None
        _LOGGER.debug("content unreadable: %s", err)
    results.append(("content", check_content(counts)))

    if os.path.isdir(integration_dir) and resources_mod.served_js_files(integration_dir):
        resources = (await ws.call("lovelace/resources"))["result"]
        files = resources_mod.served_js_files(integration_dir)
        resource_problems = check_resources(resources, files, resources_mod.served_urls(integration_dir))
    else:
        resource_problems = ["no card/ or panel/ files found in %s" % integration_dir]
    results.append(("resources", resource_problems))

    failures = []
    for name, problems in results:
        for problem in problems:
            line = "FAIL %s: %s" % (name, problem)
            failures.append(line)
            say(line)
    if not failures:
        say("verify: all %d checks passed" % len(results))
    else:
        say("verify: %d problems in %d checks" % (len(failures), sum(1 for _n, p in results if p)))
    return failures
