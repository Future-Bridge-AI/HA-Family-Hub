"""Her dashboard and her sidebar (D-18, PREV-08, ACCESS-01).

The dashboard "family-hub" is a storage-mode Lovelace dashboard with one panel-type view per
card, every view carrying an icon so the tabs fit a phone header. The sidebar step logs in as a
non-admin member (never with a stored token) and hides every panel that member can see except
Family Hub itself, so the Family Hub dashboard is all she sees (and her default panel).
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Iterable

from .client import HAClient, HAWebSocket, SeedError
from .creds import CredentialStore
from .envs import Env
from .family_file import Family, Member

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "family-hub"
DASHBOARD_ICON = "mdi:home-heart"

# Panels that stay visible in a member's sidebar (compared as whole strings: "family-hub-x" is hidden).
KEEP_PANELS = ("family-hub", "profile", "notfound")

# (title, path, icon, card) in tab order. The calendar card gets its people at runtime. Dropping the
# Pantry tab (UI-SPEC A3) is a one-entry change here.
DASHBOARD_VIEWS: tuple[tuple[str, str, str, dict[str, Any]], ...] = (
    (
        "Calendar",
        "calendar",
        "mdi:calendar-week",
        {
            "type": "custom:family-week-calendar-card",
            "recipe_entity": "todo.recipe_box",
            "meal_plan_entity": "todo.meal_plan",
            "meal_templates_entity": "todo.meal_plan_templates",
            "suggestions_entity": "todo.meal_suggestions",
            "reminders_entity": "todo.family_reminders",
        },
    ),
    ("Today", "today", "mdi:calendar-today", {"type": "custom:family-today-card"}),
    ("Chores", "chores", "mdi:broom", {"type": "custom:family-hub-chores-card", "title": "Chores"}),
    ("Rewards", "rewards", "mdi:star-circle", {"type": "custom:family-hub-rewards-card", "title": "Rewards"}),
    (
        "To-dos",
        "todos",
        "mdi:format-list-checks",
        {
            "type": "custom:family-hub-todo-card",
            "title": "To-dos",
            "entities": ["todo.groceries", "todo.errands"],
        },
    ),
    ("Recipes", "recipes", "mdi:chef-hat", {"type": "custom:family-hub-recipe-box-card", "title": "Recipes"}),
    ("Pantry", "pantry", "mdi:fridge-outline", {"type": "custom:family-hub-pantry-card", "title": "Pantry"}),
)


def build_config(env: Env, family: Family, calendars: dict[str, str]) -> dict[str, Any]:
    """The Lovelace config: a title and one panel view per DASHBOARD_VIEWS entry."""
    people = [
        {"entity": calendars[m.first_name], "name": m.first_name, "color": m.color}
        for m in family.members
        if m.first_name in calendars
    ]
    views = []
    for title, path, icon, card in DASHBOARD_VIEWS:
        card = dict(card)
        if card["type"] == "custom:family-week-calendar-card":
            card["people"] = people
        views.append({"type": "panel", "title": title, "path": path, "icon": icon, "cards": [card]})
    return {"title": env.dashboard_title, "views": views}


async def ensure_dashboard(
    ws: HAWebSocket,
    env: Env,
    family: Family,
    calendars: dict[str, str],
    say: Callable[[str], None] = print,
) -> None:
    """Create the dashboard when missing, then save its config (every run; hand edits are overwritten)."""
    listed = (await ws.call("lovelace/dashboards/list"))["result"]
    if not any(d.get("url_path") == DASHBOARD_URL_PATH for d in listed):
        await ws.call(
            "lovelace/dashboards/create",
            url_path=DASHBOARD_URL_PATH,
            title=env.dashboard_title,
            icon=DASHBOARD_ICON,
            show_in_sidebar=True,
            require_admin=False,
            mode="storage",
        )
    await ws.call("lovelace/config/save", url_path=DASHBOARD_URL_PATH, config=build_config(env, family, calendars))
    say("dashboard: %s with %d views" % (DASHBOARD_URL_PATH, len(DASHBOARD_VIEWS)))


def hidden_panels(panel_ids: Iterable[str]) -> list[str]:
    """Sorted ids to hide: everything except KEEP_PANELS (exact match). Family Hub must be listed."""
    ids = list(panel_ids)
    if "family-hub" not in ids:
        raise SeedError(
            "sidebar", "the family-hub panel is not in this member's panel list; not writing an empty sidebar"
        )
    return sorted(p for p in ids if p not in KEEP_PANELS)


async def set_member_sidebar(client: HAClient, creds: CredentialStore, member: Member) -> list[str]:
    """Hide everything but Family Hub for ``member`` and make it their default; return the hidden ids."""
    login = creds.member(member.first_name)
    token = await client.login(login["username"], login["password"])
    ws = await client.ws(token)
    panels = (await ws.call("get_panels"))["result"]
    hidden = hidden_panels(panels)
    await ws.call("frontend/set_user_data", key="sidebar", value={"panelOrder": [], "hiddenPanels": hidden})
    await ws.call("frontend/set_user_data", key="core", value={"default_panel": DASHBOARD_URL_PATH})
    await ws.close()
    return hidden
