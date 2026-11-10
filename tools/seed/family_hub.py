"""Family Hub data the seed puts in place: her pretend week, the theme and the kids' PINs.

Everything here is an idempotent top-up. Nothing is deleted and nothing a person changed is
rewritten: chores, rewards, goals, routines and pantry notes are created only when no item with the
same title (and assignee) exists, a balance is granted only while it is zero with no reward
history, recipes are written only into an empty Recipe Box, meals only for nights with no meal yet,
and list items only when missing by summary. The settings blob is replaced as a whole by the
Family Hub command, so it is always read first, changed, and written back.
"""
from __future__ import annotations

import copy
import json
import logging
from datetime import date, datetime, time, timezone, tzinfo
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

from .client import HAClient, HAWebSocket, SeedError
from .content import Content
from .creds import CredentialStore
from .entries import SETUP_PALETTE, TODO_LISTS, list_entries
from .envs import Env
from .family_file import Family

_LOGGER = logging.getLogger(__name__)

MEAL_PLAN_ENTITY = TODO_LISTS["Meal Plan"]

# Per-profile switches that make Family Hub send something. The seed writes them all off.
NOTIFICATION_FLAGS = (
    "remindersEnabled",
    "digestEnabled",
    "notifyRewardClaimed",
    "notifyChoreApproved",
    "notifyTimerAlarm",
)
SETTINGS_KEY_ALARM_DEVICES = "alarmDevices"  # const.py SETTINGS_KEY_ALARM_DEVICES

# Entries that onboarding adds and that call out to the internet (Pitfall 17).
OUTBOUND_DOMAINS = ("radio_browser", "google_translate", "met")


async def instance_today(ws: HAWebSocket) -> tuple[date, tzinfo]:
    """Today's date in the instance's own time zone (what the cards call today), and that zone."""
    config = (await ws.call("get_config"))["result"]
    try:
        zone: tzinfo = ZoneInfo(config.get("time_zone") or "UTC")
    except (KeyError, ValueError):
        zone = timezone.utc
    return datetime.now(zone).date(), zone


def due_iso(day: date, zone: tzinfo) -> str:
    """The stored due date for a chore due on ``day``: the end of that local day, as UTC ISO."""
    return datetime.combine(day, time(23, 59), tzinfo=zone).astimezone(timezone.utc).isoformat()


def dish_description(block: int) -> str:
    """The JSON a meal-plan to-do item carries in its description (the card's own shape)."""
    return json.dumps(
        {
            "description": "",
            "link": "",
            "color": "",
            "block": int(block),
            "recur": None,
            "grocyRecipeId": None,
            "servings": None,
            "spanDays": 1,
            "additionalRecipes": [],
            "leftoverDates": [],
        }
    )


async def _service(ws: HAWebSocket, domain: str, service: str, data: dict, response: bool = False) -> Any:
    reply = await ws.call(
        "call_service", domain=domain, service=service, service_data=data, return_response=response
    )
    return reply["result"].get("response") if response else None


async def todo_items(ws: HAWebSocket, entity_id: str) -> list[dict]:
    """Every item (open and completed) of a to-do list."""
    response = await _service(
        ws, "todo", "get_items", {"entity_id": entity_id, "status": ["needs_action", "completed"]}, response=True
    )
    return list(((response or {}).get(entity_id) or {}).get("items") or [])


async def _list(ws: HAWebSocket, command: str, key: str) -> list[dict]:
    reply = await ws.call(command)
    return list(reply["result"].get(key) or [])


async def get_settings(ws: HAWebSocket) -> dict:
    """Read the Family Hub settings blob; an unreadable answer is an error, never "empty"."""
    settings = (await ws.call("family_hub/get_settings"))["result"].get("settings")
    if not isinstance(settings, dict):
        raise SeedError("settings", "Family Hub settings are unreadable: %r" % (settings,))
    return settings


async def _top_up_chores(ws: HAWebSocket, user_ids: dict[str, str], content: Content, zone: tzinfo) -> int:
    have = {(c.get("title"), c.get("assigned_to")) for c in await _list(ws, "family_hub/chores/list", "chores")}
    added = 0
    for chore in content.chores:
        user_id = user_ids[chore.assignee]
        if (chore.title, user_id) in have:
            continue
        payload: dict[str, Any] = {
            "title": chore.title,
            "assigned_to": user_id,
            "star_value": chore.star_value,
            "due_date": due_iso(chore.due, zone),
            "recur_type": chore.recur_type,
            "no_approval_required": chore.no_approval_required,
            "reminder_minutes": [],  # never a reminder: nothing may notify a real phone
        }
        if chore.recur_type == "interval":
            payload["recur_interval_days"] = chore.recur_interval_days
            payload["recur_interval_unit"] = "days"
        else:
            payload["recur_weekdays"] = list(chore.recur_weekdays)
        await ws.call("family_hub/chores/create", **payload)
        added += 1
    return added


async def _top_up_rewards(ws: HAWebSocket, user_ids: dict[str, str], content: Content) -> tuple[int, int]:
    state = (await ws.call("family_hub/rewards/get_state"))["result"]
    have = {r.get("title") for r in state.get("catalog") or []}
    rewards_added = 0
    for reward in content.rewards:
        if reward.title not in have:
            await ws.call("family_hub/rewards/add_catalog_item", title=reward.title, cost_stars=reward.cost_stars)
            rewards_added += 1
    balances = state.get("balances") or {}
    history = state.get("redemptions") or []
    granted = 0
    for name, start in content.balances.items():
        user_id = user_ids[name]
        if int(balances.get(user_id) or 0) == 0 and not history:
            await ws.call(
                "family_hub/rewards/adjust_balance", user_id=user_id, delta=int(start), reason="Starting stars"
            )
            granted += 1
    return rewards_added, granted


async def _top_up_goal(ws: HAWebSocket, user_ids: dict[str, str], content: Content) -> int:
    goal = content.goal
    if goal is None:
        return 0
    user_id = user_ids[goal.assignee]
    have = {(g.get("title"), g.get("assigned_to")) for g in await _list(ws, "family_hub/goals/list", "goals")}
    if (goal.title, user_id) in have:
        return 0
    await ws.call(
        "family_hub/goals/create",
        title=goal.title,
        assigned_to=user_id,
        target_count=goal.target_count,
        star_value=goal.star_value,
    )
    return 1


async def _top_up_routines(ws: HAWebSocket, user_ids: dict[str, str], content: Content) -> int:
    have = {(i.get("user_id"), i.get("title")) for i in await _list(ws, "family_hub/routines/list", "items")}
    added = 0
    for step in content.routines:
        user_id = user_ids[step.member]
        if (user_id, step.title) in have:
            continue
        await ws.call("family_hub/routines/create", user_id=user_id, category=step.category, title=step.title)
        added += 1
    return added


async def _top_up_pantry(ws: HAWebSocket, content: Content) -> int:
    have = {e.get("name") for e in await _list(ws, "family_hub/pantry_extras/list", "extras")}
    added = 0
    for extra in content.pantry:
        if extra.name in have:
            continue
        await ws.call(
            "family_hub/pantry_extras/create",
            name=extra.name,
            quantity=extra.quantity,
            location=extra.location,
            notes=extra.notes,
        )
        added += 1
    return added


def recipe_record(recipe: Any) -> dict:
    """A Recipe Box record in the shape the Recipes card stores (see _upsertDish in the card)."""
    return {
        "uid": recipe.uid,
        "name": recipe.name,
        "description": "Ingredients: " + ", ".join(recipe.ingredients),
        "link": "",
        "rating": None,
        "grocyRecipeId": None,
        "category": "",
        "image": "",
        "steps": [{"type": "step", "text": text} for text in recipe.steps],
    }


async def _top_up_recipes(ws: HAWebSocket, content: Content) -> int:
    """The Recipes card reads the recipes store (family_hub/get_recipes), not todo.recipe_box."""
    stored = (await ws.call("family_hub/get_recipes"))["result"].get("recipes") or []
    if stored:
        return 0
    await ws.call("family_hub/set_recipes", recipes=[recipe_record(r) for r in content.recipes])
    return len(content.recipes)


async def _top_up_meals(ws: HAWebSocket, content: Content) -> int:
    planned = {str(item.get("due") or "")[:10] for item in await todo_items(ws, MEAL_PLAN_ENTITY)}
    added = 0
    for meal in content.meals:
        if meal.day.isoformat() in planned:
            continue
        await _service(
            ws,
            "todo",
            "add_item",
            {
                "entity_id": MEAL_PLAN_ENTITY,
                "item": meal.title,
                "description": dish_description(meal.block),
                "due_date": meal.day.isoformat(),
            },
        )
        added += 1
    return added


async def _top_up_items(ws: HAWebSocket, content: Content) -> int:
    added = 0
    for list_name, entity in TODO_LISTS.items():
        wanted = [i.summary for i in content.items if i.list_name == list_name]
        if not wanted:
            continue
        have = {str(item.get("summary")) for item in await todo_items(ws, entity)}
        for summary in wanted:
            if summary in have:
                continue
            await _service(ws, "todo", "add_item", {"entity_id": entity, "item": summary})
            added += 1
    return added


async def _set_pins(ws: HAWebSocket, family: Family, user_ids: dict[str, str], creds: CredentialStore) -> int:
    for child in family.children:
        await ws.call("family_hub/kiosk/set_pin", user_id=user_ids[child.first_name], pin=creds.pin(child.first_name))
    return len(family.children)


async def apply_settings(ws: HAWebSocket, family: Family, user_ids: dict[str, str], env: Env) -> None:
    """The environment's theme, kiosk sign-in for the kids and any member colour setup could not set."""
    settings = await get_settings(ws)
    settings["globalThemeId"] = env.theme
    settings["useGlobalTheme"] = True
    enabled = list(settings.get("kioskLoginEnabledUserIds") or [])
    for child in family.children:
        if user_ids[child.first_name] not in enabled:
            enabled.append(user_ids[child.first_name])
    settings["kioskLoginEnabledUserIds"] = enabled
    profiles = settings.get("userProfiles")
    if isinstance(profiles, dict):
        for member in family.members:
            profile: Optional[dict] = profiles.get(user_ids[member.first_name])
            if isinstance(profile, dict) and member.color.lower() not in SETUP_PALETTE:
                profile["color"] = member.color
    await ws.call("family_hub/set_settings", settings=settings)


async def apply_content(
    ws: HAWebSocket,
    family: Family,
    user_ids: dict[str, str],
    content: Content,
    creds: CredentialStore,
    env: Env,
    zone: tzinfo,
    say: Callable[[str], None] = print,
) -> dict[str, int]:
    """Top up everything in ``content`` and the settings; returns what was added, by area."""
    added: dict[str, int] = {}
    added["chores"] = await _top_up_chores(ws, user_ids, content, zone)
    added["rewards"], added["balances"] = await _top_up_rewards(ws, user_ids, content)
    added["goals"] = await _top_up_goal(ws, user_ids, content)
    added["routines"] = await _top_up_routines(ws, user_ids, content)
    added["pantry"] = await _top_up_pantry(ws, content)
    added["recipes"] = await _top_up_recipes(ws, content)
    added["meals"] = await _top_up_meals(ws, content)
    added["list items"] = await _top_up_items(ws, content)
    added["kid PINs"] = await _set_pins(ws, family, user_ids, creds)
    await apply_settings(ws, family, user_ids, env)
    say("content: " + ", ".join("%s +%d" % (area, count) for area, count in added.items()))
    say("theme: %s" % env.theme)
    return added


async def apply_safe_notifications(ws: HAWebSocket, say: Callable[[str], None] = print) -> bool:
    """Make sure nothing can reach a real phone or speaker (PREV-03); returns True when it changed anything.

    Atomic GET, modify, SET of the settings: every profile (and every member, even one without a
    profile yet) gets empty notify targets and every notification flag off, and the household
    alarm devices are cleared. Nothing is written when the settings are already safe.
    """
    settings = await get_settings(ws)
    before = copy.deepcopy(settings)
    profiles = settings.get("userProfiles")
    if profiles is None:
        profiles = settings["userProfiles"] = {}
    if not isinstance(profiles, dict):
        raise SeedError("settings", "Family Hub settings are unreadable: userProfiles is not a mapping")
    members = settings.get("memberUserIds")
    ids = set(profiles) | {str(m) for m in members if isinstance(m, str)} if isinstance(members, list) else set(profiles)
    for user_id in sorted(ids):
        profile = profiles.get(user_id)
        if not isinstance(profile, dict):
            profile = profiles[user_id] = {}
        profile["notifyTargets"] = []
        for flag in NOTIFICATION_FLAGS:
            profile[flag] = False
    settings[SETTINGS_KEY_ALARM_DEVICES] = []
    changed = settings != before
    if changed:
        await ws.call("family_hub/set_settings", settings=settings)
    say("notifications: %d profiles safe (targets empty, alerts off)%s" % (len(ids), "" if changed else ", unchanged"))
    return changed


async def remove_outbound_entries(
    client: HAClient, token: str, say: Callable[[str], None] = print
) -> int:
    """Delete the config entries onboarding adds that call out to the internet; returns how many."""
    removed = 0
    for entry in await list_entries(client, token):
        if entry.get("domain") not in OUTBOUND_DOMAINS:
            continue
        status, body = await client.rest(
            "DELETE", "/api/config/config_entries/entry/%s" % entry["entry_id"], token=token
        )
        if status != 200:
            raise SeedError("entries", "deleting the %s entry failed (HTTP %s): %s" % (entry.get("domain"), status, body))
        removed += 1
    say("outbound entries removed: %d" % removed)
    return removed
