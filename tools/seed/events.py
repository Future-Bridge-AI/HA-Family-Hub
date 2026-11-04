"""Week-anchored pretend calendar events, synced by diff (PREV-04, D-11, D-15, D-25).

The events land on calendars that may be the family's real Google calendars, so two things
matter more than anything else here:

* Nothing but an exact tagged, marked, single, in-window event on an allow-listed calendar is
  ever deleted. ``diff`` sends every existing event through ``calendar_tags.matches`` first and
  builds its delete list from the survivors only; there is no other delete path in this module.
* A refresh must not churn the family's phones. The desired set covers this ISO week and the
  next one, every event has a stable key (ISO year and week, weekday, slot, person), and
  ``diff`` creates only what is missing and deletes only what is stale, so a second sync on the
  same day reports "create 0, delete 0". Next week's template is a subset of this week's with
  identical times and titles, so when Monday rolls over the new plan only adds events.

Dry run is the default for ``sync`` and ``clean``: nothing is written without ``--apply``.

Run: python -m tools.seed.events --target {dev,preview} {plan,sync,clean}
         --calendar calendar.sam=Sam [--calendar calendar.old=Old:ro ...] [--today YYYY-MM-DD] [--apply]
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import datetime
import logging
import re
import sys
from typing import Any, Callable, Mapping, Optional
from urllib.parse import quote

from . import calendar_tags
from .bootstrap import open_admin
from .client import HAClient, SeedError
from .creds import CredentialStore
from .envs import ENVIRONMENTS, Env, GuardRefused, base_url, get_env

_LOGGER = logging.getLogger(__name__)

Say = Callable[[str], None]

WINDOW_DAYS = 14
LOOKBACK_DAYS = 28
MAX_CALENDARS = 12


@dataclasses.dataclass(frozen=True)
class CalendarSlot:
    """One calendar entity that belongs to a family member; read-only ones never get events."""

    person: str
    entity_id: str
    writable: bool = True


@dataclasses.dataclass(frozen=True)
class DesiredEvent:
    """One event the seed wants to exist. All-day events start at local midnight, end a day later."""

    key: str
    entity_id: str
    summary: str
    description: str
    start: datetime.datetime
    end: datetime.datetime
    all_day: bool

    def sort_key(self) -> tuple:
        return (self.start, self.entity_id, self.key)


@dataclasses.dataclass(frozen=True)
class SeededEvent:
    """An existing event that passed the matcher: it is ours and may be kept or deleted."""

    entity_id: str
    uid: str
    key: str
    summary: str
    start: calendar_tags.EventTime
    recurrence_id: Optional[str] = None

    def sort_key(self) -> tuple:
        return (calendar_tags.as_naive_datetime(self.start), self.entity_id, self.key, self.uid)


@dataclasses.dataclass
class Diff:
    """What a sync would do. ``keep`` events are already right and are left untouched."""

    create: list[DesiredEvent] = dataclasses.field(default_factory=list)
    delete: list[SeededEvent] = dataclasses.field(default_factory=list)
    keep: list[SeededEvent] = dataclasses.field(default_factory=list)


# -- the weekly templates --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _Template:
    weekday: int  # 1 = Monday .. 7 = Sunday
    slot: int  # position within the day; part of the key
    members: tuple  # template member indexes; more than one means a shared event
    title: str
    start: Optional[datetime.time]  # None = all-day
    minutes: int = 60


def _t(hour: int, minute: int = 0) -> datetime.time:
    return datetime.time(hour, minute)


# Template members: 0 = first parent, 1 = second parent, 2 = older child, 3 = younger child. They map
# onto the writable calendars in order (modulo how many there are). With four or more writable
# calendars every day leaves at least one member without events (the "partial" rule).
THIS_WEEK: tuple = (
    _Template(1, 1, (2,), "School drop-off", _t(8, 30), 30),
    _Template(1, 2, (2,), "Piano lesson", _t(16, 30), 45),
    _Template(2, 1, (3,), "School drop-off", _t(8, 30), 30),
    _Template(2, 2, (2,), "Football practice", _t(17, 0), 60),
    _Template(3, 1, (2,), "Dentist", _t(10, 0), 60),
    _Template(3, 2, (0, 1), "Family movie night", _t(18, 30), 150),
    _Template(4, 1, (3,), "School drop-off", _t(8, 30), 30),
    _Template(4, 2, (3,), "Piano lesson", _t(16, 30), 45),
    _Template(5, 1, (1,), "Grandma visits", None),
    _Template(5, 2, (2,), "Football practice", _t(17, 0), 60),
    _Template(6, 1, (2,), "Football practice", _t(9, 0), 90),
    _Template(6, 2, (3,), "Piano lesson", _t(11, 0), 45),
    _Template(6, 3, (1,), "Grandma visits", _t(14, 0), 120),
    _Template(6, 4, (2,), "Football practice", _t(16, 30), 60),
    _Template(7, 1, (3,), "Piano lesson", _t(10, 0), 45),
    _Template(7, 2, (0,), "Family movie night", _t(18, 0), 120),
)

# Next week: no events on Sunday and a single event on Tuesday, everything else as this week. Built
# by filtering THIS_WEEK so every key, time and title is identical and a rollover only adds events.
_NEXT_WEEK_DROPPED = {(7, 1), (7, 2), (2, 2)}
NEXT_WEEK: tuple = tuple(t for t in THIS_WEEK if (t.weekday, t.slot) not in _NEXT_WEEK_DROPPED)


def monday_of(today: datetime.date) -> datetime.date:
    return today - datetime.timedelta(days=today.weekday())


def window(today: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """The span events are planned for: [Monday of this week, Monday of the week after next)."""
    monday = datetime.datetime.combine(monday_of(today), datetime.time.min)
    return monday, monday + datetime.timedelta(days=WINDOW_DAYS)


def delete_window(today: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """The only span in which an old seeded event may be deleted: four more weeks back."""
    start, end = window(today)
    return start - datetime.timedelta(days=LOOKBACK_DAYS), end


def _slug(person: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", person.lower()) or "member"


def plan_week_events(slots: list[CalendarSlot], env: Env, today: datetime.date) -> list[DesiredEvent]:
    """Build the desired events for this week and next over the writable slots, sorted and stable."""
    writable = [slot for slot in slots if slot.writable]
    if not writable:
        return []
    monday = monday_of(today)
    desired: dict[tuple[str, str], DesiredEvent] = {}
    for week, template in ((0, THIS_WEEK), (1, NEXT_WEEK)):
        week_monday = monday + datetime.timedelta(days=7 * week)
        iso = week_monday.isocalendar()
        for item in template:
            day = week_monday + datetime.timedelta(days=item.weekday - 1)
            targets: list[CalendarSlot] = []
            for member in item.members:
                slot = writable[member % len(writable)]
                if slot not in targets:
                    targets.append(slot)
            shared = len(item.members) > 1
            for slot in targets:
                who = "shared" if shared else _slug(slot.person)
                key = "%dw%02d-%d-%d-%s" % (iso[0], iso[1], item.weekday, item.slot, who)
                if item.start is None:
                    start = datetime.datetime.combine(day, datetime.time.min)
                    end = start + datetime.timedelta(days=1)
                else:
                    start = datetime.datetime.combine(day, item.start)
                    end = start + datetime.timedelta(minutes=item.minutes)
                desired[(slot.entity_id, key)] = DesiredEvent(
                    key=key,
                    entity_id=slot.entity_id,
                    summary=env.tag + item.title,
                    description=calendar_tags.marker(env, key),
                    start=start,
                    end=end,
                    all_day=item.start is None,
                )
    return sorted(desired.values(), key=DesiredEvent.sort_key)


# -- the diff --------------------------------------------------------------------------------------


def _same(existing: SeededEvent, wanted: DesiredEvent) -> bool:
    """An existing event is right when its summary and start (or all-day date) are the wanted ones."""
    if existing.summary != wanted.summary:
        return False
    if wanted.all_day:
        return (
            not isinstance(existing.start, datetime.datetime)
            and isinstance(existing.start, datetime.date)
            and existing.start == wanted.start.date()
        )
    return isinstance(existing.start, datetime.datetime) and existing.start == wanted.start


def diff(
    desired: list[DesiredEvent],
    existing: Mapping[str, list[Mapping[str, Any]]],
    env: Env,
    allowed: Any,
    today: datetime.date,
) -> Diff:
    """Compare the desired events with what each calendar holds, per (calendar, key).

    ``existing`` maps an entity id to the events HA returned for it. Every one is first passed
    through ``calendar_tags.matches``; an event that fails it is in no list at all. Of the matching
    events per key: one that is exactly right is kept, the rest (stale keys, duplicates, moved or
    renamed events) are deleted, and anything desired without a keeper is created.
    """
    window_start, window_end = delete_window(today)
    found: dict[tuple[str, str], list[SeededEvent]] = {}
    for entity_id, events in existing.items():
        for raw in events:
            if not calendar_tags.matches(raw, env, entity_id, allowed, window_start, window_end):
                continue
            start = calendar_tags.event_start(raw)
            key = calendar_tags.parse_marker(raw.get("description"), env)
            if start is None or key is None:  # matches() already guaranteed both
                continue
            found.setdefault((entity_id, key), []).append(
                SeededEvent(
                    entity_id=entity_id,
                    uid=str(raw.get("uid") or ""),
                    key=key,
                    summary=raw["summary"],
                    start=start,
                    recurrence_id=raw.get("recurrence_id") or None,
                )
            )
    wanted = {(event.entity_id, event.key): event for event in desired if event.entity_id in allowed}
    result = Diff()
    for pair, events in found.items():
        events.sort(key=SeededEvent.sort_key)
        target = wanted.get(pair)
        keeper = next((event for event in events if target is not None and _same(event, target)), None)
        for event in events:
            (result.keep if event is keeper else result.delete).append(event)
    for pair, event in wanted.items():
        if not any(kept.entity_id == pair[0] and kept.key == pair[1] for kept in result.keep):
            result.create.append(event)
    result.create.sort(key=DesiredEvent.sort_key)
    result.delete.sort(key=SeededEvent.sort_key)
    result.keep.sort(key=SeededEvent.sort_key)
    return result


# -- talking to Home Assistant ---------------------------------------------------------------------


def _line(verb: str, entity_id: str, start: Any, summary: str) -> str:
    if isinstance(start, datetime.datetime):
        text = start.strftime("%Y-%m-%dT%H:%M")
    else:
        text = start.isoformat()
    return "%s %s %s %s" % (verb, entity_id, text, summary)


async def read_events(
    client: HAClient, token: str, entity_id: str, start: datetime.datetime, end: datetime.datetime
) -> list[dict]:
    """Read one calendar's events over [start, end) through GET /api/calendars/<entity>."""
    path = "/api/calendars/%s?start=%s&end=%s" % (
        quote(entity_id, safe=""),
        quote(start.isoformat(), safe=""),
        quote(end.isoformat(), safe=""),
    )
    status, body = await client.rest("GET", path, token=token)
    if status != 200 or not isinstance(body, list):
        raise SeedError("calendar_read", "cannot read events of %s (HTTP %s): %s" % (entity_id, status, body))
    return body


async def create_event(client: HAClient, token: str, event: DesiredEvent) -> None:
    """Create one event through the calendar.create_event service."""
    payload: dict[str, Any] = {
        "entity_id": event.entity_id,
        "summary": event.summary,
        "description": event.description,
    }
    if event.all_day:
        payload["start_date"] = event.start.date().isoformat()
        payload["end_date"] = event.end.date().isoformat()
    else:
        payload["start_date_time"] = event.start.strftime("%Y-%m-%d %H:%M:%S")
        payload["end_date_time"] = event.end.strftime("%Y-%m-%d %H:%M:%S")
    status, body = await client.rest("POST", "/api/services/calendar/create_event", json=payload, token=token)
    if status != 200:
        raise SeedError("calendar_create", "creating %s on %s failed (HTTP %s): %s" % (event.key, event.entity_id, status, body))


async def _run(
    client: HAClient,
    token: str,
    slots: list[CalendarSlot],
    env: Env,
    today: datetime.date,
    apply: bool,
    desired: list[DesiredEvent],
    say: Say,
) -> Diff:
    writable = [slot for slot in slots if slot.writable]
    allowed = frozenset(slot.entity_id for slot in writable)
    suffix = "(applied)" if apply else "(dry run)"
    if not writable:
        say("no writable calendars: nothing to do")
        say("events: create 0, delete 0, keep 0 %s" % suffix)
        return Diff()
    window_start, window_end = delete_window(today)
    existing = {
        slot.entity_id: await read_events(client, token, slot.entity_id, window_start, window_end)
        for slot in writable
    }
    result = diff(desired, existing, env, allowed, today)
    for event in result.delete:
        say(_line("DELETE", event.entity_id, event.start, event.summary))
    for event in result.create:
        say(_line("CREATE", event.entity_id, event.start, event.summary))
    for event in result.keep:
        say(_line("KEEP", event.entity_id, event.start, event.summary))
    if apply:
        if result.delete:
            ws = await client.ws(token)
            for event in result.delete:
                fields: dict[str, Any] = {"entity_id": event.entity_id, "uid": event.uid}
                if event.recurrence_id:
                    fields["recurrence_id"] = event.recurrence_id
                await ws.call("calendar/event/delete", **fields)
        for event in result.create:
            await create_event(client, token, event)
    say("events: create %d, delete %d, keep %d %s" % (len(result.create), len(result.delete), len(result.keep), suffix))
    return result


async def sync(
    client: HAClient,
    token: str,
    slots: list[CalendarSlot],
    env: Env,
    today: datetime.date,
    apply: bool,
    say: Say = print,
) -> Diff:
    """Make each writable calendar hold exactly the planned events: create missing, delete stale."""
    return await _run(client, token, slots, env, today, apply, plan_week_events(slots, env, today), say)


async def clean(
    client: HAClient,
    token: str,
    slots: list[CalendarSlot],
    env: Env,
    today: datetime.date,
    apply: bool,
    say: Say = print,
) -> Diff:
    """Delete every matching seeded event in the delete window (the desired set is empty)."""
    return await _run(client, token, slots, env, today, apply, [], say)


# -- command line ----------------------------------------------------------------------------------


def parse_calendar(text: str) -> CalendarSlot:
    """Parse ``ENTITY=PERSON`` or ``ENTITY=PERSON:ro``."""
    entity_id, sep, person = text.partition("=")
    writable = True
    if person.endswith(":ro"):
        person, writable = person[: -len(":ro")], False
    if not sep or not re.fullmatch(r"calendar\.[a-z0-9_]+", entity_id) or not person.strip():
        raise argparse.ArgumentTypeError("--calendar expects calendar.ENTITY=PERSON[:ro], got %r" % text)
    return CalendarSlot(person=person.strip(), entity_id=entity_id, writable=writable)


def _say(line: str) -> None:
    print(line, flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.seed.events", description=__doc__.split("\n")[0])
    parser.add_argument("--target", required=True, choices=sorted(ENVIRONMENTS))
    parser.add_argument("--base-url", default=None, help="override; must be https on a loopback host")
    parser.add_argument("--ca", default="dev/.ha-certs/ca.crt")
    parser.add_argument("--secrets-dir", default="dev/.ha-secrets")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("plan", "print the planned events, touch nothing"),
        ("sync", "create missing and delete stale tagged events (dry run unless --apply)"),
        ("clean", "delete every tagged event of this target (dry run unless --apply)"),
    ):
        sp = sub.add_parser(name, help=text)
        sp.add_argument("--calendar", action="append", type=parse_calendar, default=[], help="ENTITY=PERSON[:ro]")
        sp.add_argument("--today", type=datetime.date.fromisoformat, default=None, help="YYYY-MM-DD")
        if name != "plan":
            sp.add_argument("--apply", action="store_true", help="really write; the default is a dry run")
    return parser


async def _main_async(args: argparse.Namespace, env: Env, url: str, today: datetime.date) -> int:
    slots: list[CalendarSlot] = args.calendar
    if args.command == "plan":
        for event in plan_week_events(slots, env, today):
            _say("%s %s %s %s" % (event.entity_id, event.start.strftime("%Y-%m-%dT%H:%M"), event.summary, event.key))
        return 0
    async with HAClient(url, args.ca) as client:
        token, _ws = await open_admin(client, env, CredentialStore(args.secrets_dir, env.key))
        runner = sync if args.command == "sync" else clean
        await runner(client, token, slots, env, today, args.apply, _say)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        env = get_env(args.target)
        url = base_url(env, args.base_url)
        if len(args.calendar) > MAX_CALENDARS:
            raise GuardRefused("refusing %d calendars (at most %d)" % (len(args.calendar), MAX_CALENDARS))
        if len({slot.entity_id for slot in args.calendar}) != len(args.calendar):
            raise GuardRefused("a calendar was named twice")
        today = args.today or datetime.date.today()
        return asyncio.run(_main_async(args, env, url, today))
    except GuardRefused as err:
        print("refused: %s" % err, file=sys.stderr)
        return err.exit_code
    except SeedError as err:
        print("error [%s]: %s" % (err.code, err.message), file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    sys.exit(main())
