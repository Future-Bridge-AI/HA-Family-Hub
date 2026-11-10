"""Config entries the seed creates: the to-do lists, a Local Calendar per member and Family Hub.

Everything goes through the same config flows a person would click through (drive_config_flow),
and every ensure_* function does nothing when its entry already exists, so a second seed is a
top-up. Entity ids are read from the entity registry rather than guessed from a name.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable, Optional

from . import events
from .client import HAClient, HAWebSocket, SeedError
from .family_file import Family

_LOGGER = logging.getLogger(__name__)

# The five lists the cards need, plus the two plain lists her To-dos tab shows. Order matters
# only for the console output.
TODO_LISTS: dict[str, str] = {
    "Recipe Box": "todo.recipe_box",
    "Meal Plan": "todo.meal_plan",
    "Meal Plan Templates": "todo.meal_plan_templates",
    "Meal Suggestions": "todo.meal_suggestions",
    "Family Reminders": "todo.family_reminders",
    "Groceries": "todo.groceries",
    "Errands": "todo.errands",
}

NOTIFY_TARGET = "notify.persistent_notification"

# The six board colours Family Hub's setup form accepts for a member (config_flow's palette).
# Any other colour from the family file is applied to the member's profile after setup instead.
SETUP_PALETTE = ("#7ec9d9", "#9ed97e", "#b07ed9", "#d97e9e", "#d9a67e", "#d9bf7e")


async def list_entries(client: HAClient, token: str, domain: Optional[str] = None) -> list[dict]:
    """List config entries (optionally one domain) through the REST API."""
    path = "/api/config/config_entries/entry"
    if domain:
        path += "?domain=%s" % domain
    status, body = await client.rest("GET", path, token=token)
    if status != 200 or not isinstance(body, list):
        raise SeedError("http", "listing config entries failed (HTTP %s): %s" % (status, body))
    return body


async def entity_for_entry(ws: HAWebSocket, entry_id: str, domain: str, timeout: float = 90.0) -> str:
    """Wait until the entry's ``domain`` entity is in the entity registry and return its id."""
    deadline = time.monotonic() + timeout
    while True:
        registry = (await ws.call("config/entity_registry/list"))["result"]
        for item in registry:
            if item.get("config_entry_id") == entry_id and str(item.get("entity_id", "")).startswith(domain + "."):
                return item["entity_id"]
        if time.monotonic() >= deadline:
            raise SeedError("timeout", "no %s entity appeared for config entry %s" % (domain, entry_id))
        await asyncio.sleep(0.5)


async def _create_entry(
    client: HAClient, token: str, handler: str, title: str, answers: dict
) -> dict:
    """Run a config flow and return the new entry (found again by domain and title)."""
    await client.drive_config_flow(token, handler, answers)
    for entry in await list_entries(client, token, handler):
        if entry.get("title") == title:
            return entry
    raise SeedError("flow", "config flow %s finished but no entry titled %r exists" % (handler, title))


async def ensure_todo_lists(
    client: HAClient, token: str, ws: HAWebSocket, say: Callable[[str], None] = print
) -> dict[str, str]:
    """Create each missing Local To-do list and return ``list name -> entity id``."""
    existing = {e.get("title"): e for e in await list_entries(client, token, "local_todo")}
    created = 0
    entities: dict[str, str] = {}
    for name, expected in TODO_LISTS.items():
        entry = existing.get(name)
        if entry is None:
            entry = await _create_entry(client, token, "local_todo", name, {"user": {"todo_list_name": name}})
            created += 1
        entity = await entity_for_entry(ws, entry["entry_id"], "todo")
        if entity != expected:
            raise SeedError("entries", "to-do list %r has entity %s, the cards expect %s" % (name, entity, expected))
        entities[name] = entity
    say("to-do lists: %d present (%d created)" % (len(entities), created))
    return entities


async def ensure_local_calendars(
    client: HAClient, token: str, ws: HAWebSocket, family: Family, say: Callable[[str], None] = print
) -> dict[str, str]:
    """Create a Local Calendar for each member whose calendar is "local"; ``first_name -> entity id``."""
    existing = {e.get("title"): e for e in await list_entries(client, token, "local_calendar")}
    created = 0
    calendars: dict[str, str] = {}
    for member in family.members:
        if not member.local_calendar:
            continue
        entry = existing.get(member.first_name)
        if entry is None:
            entry = await _create_entry(
                client, token, "local_calendar", member.first_name, {"user": {"calendar_name": member.first_name}}
            )
            created += 1
        calendars[member.first_name] = await entity_for_entry(ws, entry["entry_id"], "calendar")
    say("calendars: %d local (%d created)" % (len(calendars), created))
    return calendars


async def _wait_for_family_hub(ws: HAWebSocket, timeout: float = 90.0) -> dict:
    """Return the Family Hub settings once the entry has loaded (get_settings answers not_found before)."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            settings = (await ws.call("family_hub/get_settings"))["result"]["settings"]
            if isinstance(settings, dict):
                return settings
        except SeedError as err:
            if err.code != "not_found":
                raise
        if time.monotonic() >= deadline:
            raise SeedError("timeout", "Family Hub did not finish loading")
        await asyncio.sleep(1)


def _member_profile_answer(family: Family, calendars: dict[str, str]) -> Callable[[dict], dict]:
    """Answer one member_profile form: the form names the member in its description placeholders."""

    def answer(step: dict) -> dict:
        name = (step.get("description_placeholders") or {}).get("member_name")
        try:
            member = family.member(name)
        except KeyError:
            raise SeedError("flow", "Family Hub asked about an unknown member %r" % name) from None
        color = member.color.lower()
        if color not in SETUP_PALETTE:
            color = SETUP_PALETTE[family.members.index(member) % len(SETUP_PALETTE)]
        result: dict = {"member_color": color, "member_include_in_chores": member.is_child}
        if member.first_name in calendars:
            result["member_calendar"] = calendars[member.first_name]
        return result

    return answer


async def ensure_family_hub_entry(
    client: HAClient,
    token: str,
    ws: HAWebSocket,
    family: Family,
    user_ids: dict[str, str],
    calendars: dict[str, str],
    say: Callable[[str], None] = print,
) -> None:
    """Set up Family Hub through its own config flow, or check that an existing entry is ours."""
    entries = await list_entries(client, token, "family_hub")
    if not entries:
        await client.drive_config_flow(
            token,
            "family_hub",
            {
                "features": {"setup_features": ["chores"]},
                "users": {"initial_member_user_ids": [user_ids[m.first_name] for m in family.members]},
                "member_profile": _member_profile_answer(family, calendars),
                "chores_features": {"routines_enabled": True, "goals_in_chores": True, "goals_in_rewards": True},
                "calendars": {"calendars": []},
                "notifications": {"default_notify_target": NOTIFY_TARGET},
                "dashboard": {"add_dashboard": False},
                "finish": {},
            },
        )
        await _wait_for_family_hub(ws)
        say("family hub: set up through its config flow")
        return
    settings = await _wait_for_family_hub(ws)
    known = set(settings.get("memberUserIds") or [])
    missing = [m.first_name for m in family.members if user_ids[m.first_name] not in known]
    if missing:
        raise SeedError(
            "entries", "this instance was set up by hand; run the reset (not Family Hub members: %s)" % ", ".join(missing)
        )
    say("family hub: already set up (%d members)" % len(family.members))


def calendar_slots(
    family: Family, calendars: dict[str, str], google_slots: tuple = ()
) -> list[events.CalendarSlot]:
    """The calendars the pretend events go on: one writable slot per member with a Local Calendar,
    plus the Google slots (google.google_slots), each with its own writable flag.

    ``calendars`` is what ensure_local_calendars returned (``first_name -> entity id``). Members
    whose calendar is not local, or whose calendar entity does not exist, get no local slot. The
    event sync writes to, and may delete from, only the writable slots of this list.
    """
    local = [
        events.CalendarSlot(person=member.first_name, entity_id=calendars[member.first_name], writable=True)
        for member in family.members
        if member.local_calendar and member.first_name in calendars
    ]
    return local + list(google_slots)
