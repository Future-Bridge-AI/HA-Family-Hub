"""Back up every chosen Google calendar before anything destructive runs (D-08, D-30).

Dev and Preview are connected read and write to the family's real calendars, so a deploy, a reset or a
refresh must never run unless every chosen calendar has just been saved to a file that can be restored
from. Each calendar is exported from the secret iCal address its owner copied from Google Calendar
(Settings > Integrate calendar), into ``<backups dir>/<env>/<YYYY-MM-DD_HHMMSS>/<key>.ics``.

The export is only accepted when it really is a calendar: HTTP 200, a non-empty body that starts with
``BEGIN:VCALENDAR`` and contains ``END:VCALENDAR``. Anything else (a 404 for a changed address, an HTML
sign-in page, an empty or cut-off answer, a network failure) raises BackupError, which stops the calling
script before it stops, wipes or deletes anything. A calendar the developer does not own has no such
address; with ``backup: ha-snapshot`` in the family file its events are written as JSON from the
running instance instead.

The secret address is a credential. It is used only to fetch, never printed, logged or put in an
error message: everything here names a calendar by its ``key``.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import shutil
import ssl
import urllib.error
import urllib.request
from typing import Any, Callable, Optional
from urllib.parse import quote

from .client import HAClient, HAWebSocket, SeedError
from . import google as google_mod

_LOGGER = logging.getLogger(__name__)

STAMP_FORMAT = "%Y-%m-%d_%H%M%S"
NO_CALENDARS = "backup: no Google calendars configured"
FETCH_TIMEOUT = 30.0
SNAPSHOT_PAST_DAYS = 90
SNAPSHOT_FUTURE_DAYS = 365

_CALENDAR_START = "BEGIN:VCALENDAR"
_CALENDAR_END = "END:VCALENDAR"


class BackupError(Exception):
    """A backup failed; nothing may be stopped, wiped or deleted (exit code 5)."""

    exit_code = 5

    def __init__(self, key: str, reason: str) -> None:
        super().__init__("backup failed for %s: %s - nothing was changed" % (key, reason))
        self.key = key
        self.reason = reason


def default_fetch(url: str) -> tuple[int, str]:
    """GET the address with a 30 s timeout and the system certificate store; return (status, body)."""
    request = urllib.request.Request(url, headers={"User-Agent": "family-hub-seed-backup"})
    try:
        with urllib.request.urlopen(request, timeout=FETCH_TIMEOUT, context=ssl.create_default_context()) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        return err.code, ""


def _calendar_problem(body: str) -> Optional[str]:
    """Why the answer is not a usable calendar file, or None when it is one."""
    if not body.strip():
        return "the calendar file is empty"
    if not body.lstrip("﻿").startswith(_CALENDAR_START):
        return "the answer is not a calendar file (it does not start with %s)" % _CALENDAR_START
    if _CALENDAR_END not in body:
        return "the calendar file is cut off (there is no %s)" % _CALENDAR_END
    return None


def _write_private_file(path: str, text: str) -> None:
    """Write ``text`` as it is (line endings untouched) with mode 0600."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
        os.fchmod(fd, 0o600)
        handle.write(text)


def _fetch_ics(calendar: dict, fetch: Callable[[str], tuple[int, str]]) -> str:
    key = calendar["key"]
    try:
        status, body = fetch(calendar["ical_secret_url"])
    except Exception as err:  # the exception text can carry the address, so only its type is reported
        raise BackupError(key, "the calendar could not be fetched (%s)" % type(err).__name__) from None
    if status != 200:
        raise BackupError(key, "Google answered HTTP %s instead of the calendar" % status)
    problem = _calendar_problem(body)
    if problem:
        raise BackupError(key, problem)
    return body


def _read_snapshot(calendar: dict, snapshot: Optional[Callable[[dict], Any]]) -> Any:
    key = calendar["key"]
    if snapshot is None:
        raise BackupError(key, "the snapshot of this calendar needs the running instance, which is not available")
    try:
        data = snapshot(calendar)
    except BackupError:
        raise
    except Exception:
        raise BackupError(key, "the snapshot could not be read from the running instance") from None
    if not data:
        raise BackupError(key, "the snapshot of this calendar is not available (is the instance running and signed in?)")
    return data


def _free_folder(base: str, stamp: str) -> str:
    """base/stamp, or base/stamp_2, _3 ... when two backups land in the same second."""
    candidate = os.path.join(base, stamp)
    number = 2
    while os.path.exists(candidate):
        candidate = os.path.join(base, "%s_%d" % (stamp, number))
        number += 1
    return candidate


def backup_calendars(
    family: Any,
    env: Any,
    out_root: str,
    now: datetime.datetime,
    fetch: Optional[Callable[[str], tuple[int, str]]] = None,
    snapshot: Optional[Callable[[dict], Any]] = None,
) -> str:
    """Save every chosen calendar and return the line to print; raise BackupError on any failure.

    The files are written into a ``.partial`` folder that takes its final dated name only after every
    calendar succeeded, so a folder with a date on it is always a complete backup. ``fetch`` and
    ``snapshot`` are injected by the tests.
    """
    calendars = family.google["calendars"] if family.google else []
    if not calendars:
        return NO_CALENDARS
    fetch = fetch or default_fetch
    env_key = env if isinstance(env, str) else env.key
    base = os.path.join(out_root, env_key)
    for directory in (out_root, base):
        os.makedirs(directory, mode=0o700, exist_ok=True)
        os.chmod(directory, 0o700)
    final = _free_folder(base, now.strftime(STAMP_FORMAT))
    staging = final + ".partial"
    os.mkdir(staging, 0o700)
    try:
        for calendar in calendars:
            key = calendar["key"]
            if calendar["backup"] == "ical":
                _write_private_file(os.path.join(staging, "%s.ics" % key), _fetch_ics(calendar, fetch))
            else:
                data = _read_snapshot(calendar, snapshot)
                _write_private_file(os.path.join(staging, "%s.json" % key), json.dumps(data, indent=2, sort_keys=True) + "\n")
        os.rename(staging, final)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return "backup: %d calendars -> %s" % (len(calendars), final)


async def read_snapshots(
    client: HAClient, token: str, ws: HAWebSocket, family: Any, now: datetime.datetime
) -> dict[str, Optional[dict]]:
    """Read the events of every ``backup: ha-snapshot`` calendar from the running instance.

    ``key -> {calendar_id, entity_id, taken_at, window, events}``, or None for a calendar whose
    entity is not there or whose events could not be read.
    """
    wanted = [c for c in family.google["calendars"] if c["backup"] == "ha-snapshot"]
    result: dict[str, Optional[dict]] = {c["key"]: None for c in wanted}
    entries = [e for e in await google_mod.google_entries(client, token) if e.get("state") == "loaded"]
    if not entries:
        return result
    registry = (await ws.call("config/entity_registry/list"))["result"]
    entities = google_mod.entity_map(registry, entries[0]["unique_id"], family.google)
    utc = datetime.timezone.utc
    start = (now.astimezone(utc) - datetime.timedelta(days=SNAPSHOT_PAST_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (now.astimezone(utc) + datetime.timedelta(days=SNAPSHOT_FUTURE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for calendar in wanted:
        entity_id = entities.get(calendar["key"])
        if entity_id is None:
            continue
        status, body = await client.rest(
            "GET", "/api/calendars/%s?start=%s&end=%s" % (entity_id, quote(start), quote(end)), token=token
        )
        if status == 200 and isinstance(body, list):
            result[calendar["key"]] = {
                "calendar_id": calendar["calendar_id"],
                "entity_id": entity_id,
                "taken_at": now.astimezone(utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "window": [start, end],
                "events": body,
            }
    return result
