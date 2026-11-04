"""The family file: who is in the family Dev and Preview are seeded for (D-12).

``tools/seed/family.local.yaml`` (gitignored) holds the real family; when it is absent the
committed, invented ``tools/seed/data/family.example.yaml`` is used. The file is validated
strictly: every problem raises FamilyFileError naming the key path (for example
``members[2].age``) so a typo is found before anything is written to Home Assistant.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Any, Callable, Optional

from .creds import ADMIN_USERNAME

SEED_DIR = Path(__file__).resolve().parent
LOCAL_FILE = SEED_DIR / "family.local.yaml"
EXAMPLE_FILE = SEED_DIR / "data" / "family.example.yaml"

SCHEMA_VERSION = 1
_TOP_KEYS = ("schema_version", "members", "google")
_MEMBER_KEYS = ("first_name", "role", "admin", "age", "color", "calendar")
_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z' -]{0,30}$")
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_ROLES = ("parent", "child")
_AGE_MIN, _AGE_MAX = 3, 17
_GOOGLE_KEYS = ("client_id", "client_secret", "calendars")
_GOOGLE_CALENDAR_KEYS = ("key", "calendar_id", "person", "writable", "expect_events", "backup", "ical_secret_url")
_CALENDAR_KEY_RE = re.compile(r"^[a-z0-9-]+$")
_BACKUP_KINDS = ("ical", "ha-snapshot")
_ICAL_URL_PREFIX = "https://calendar.google.com/calendar/ical/"


class FamilyFileError(Exception):
    """The family file is unusable (exit code 2); the message names the key path."""

    exit_code = 2


@dataclasses.dataclass(frozen=True)
class Member:
    """One family member as the seed uses them."""

    first_name: str
    username: str
    role: str
    admin: bool
    age: Optional[int]
    color: str
    calendar: str

    @property
    def is_child(self) -> bool:
        return self.role == "child"

    @property
    def local_calendar(self) -> bool:
        return self.calendar == "local"


@dataclasses.dataclass(frozen=True)
class Family:
    """The validated family: members in file order, the google block, and where it came from."""

    members: tuple[Member, ...]
    google: Optional[dict] = None
    source: str = ""

    @property
    def children(self) -> tuple[Member, ...]:
        return tuple(m for m in self.members if m.is_child)

    def member(self, first_name: str) -> Member:
        for member in self.members:
            if member.first_name == first_name:
                return member
        raise KeyError(first_name)


def username_for(first_name: str) -> str:
    """The login name: the lower-cased first name with every non-letter removed."""
    return re.sub(r"[^a-z]", "", first_name.lower())


def her(family: Family) -> Member:
    """The family product owner's member: the first parent who is not the admin."""
    for member in family.members:
        if member.role == "parent" and not member.admin:
            return member
    raise FamilyFileError("members: no non-admin parent")


def _reject_unknown(mapping: dict, allowed: tuple[str, ...], path: str) -> None:
    for key in mapping:
        if key not in allowed:
            raise FamilyFileError("%s: unknown key %r (allowed: %s)" % (path or "file", key, ", ".join(allowed)))


def _parse_google_calendar(raw: Any, index: int) -> dict:
    """One entry of google.calendars, normalised: flags default to false and backup to "ical".

    Error messages never contain ``ical_secret_url``: it is a secret address (anyone holding it can
    read the calendar), and a message ends up in a terminal, a log or a chat.
    """
    path = "google.calendars[%d]" % index
    if not isinstance(raw, dict):
        raise FamilyFileError("%s: must be a mapping" % path)
    _reject_unknown(raw, _GOOGLE_CALENDAR_KEYS, path)

    key = raw.get("key")
    if not isinstance(key, str) or not _CALENDAR_KEY_RE.match(key):
        raise FamilyFileError("%s.key: %r must use only lower-case letters, digits and hyphens" % (path, key))
    calendar_id = raw.get("calendar_id")
    if not isinstance(calendar_id, str) or not calendar_id.strip():
        raise FamilyFileError("%s.calendar_id: the Google Calendar ID is needed (Settings > Integrate calendar)" % path)
    person = raw.get("person")
    if not isinstance(person, str) or not person.strip():
        raise FamilyFileError("%s.person: the first name of the member this calendar belongs to is needed" % path)
    flags = {}
    for name in ("writable", "expect_events"):
        value = raw.get(name, False)
        if not isinstance(value, bool):
            raise FamilyFileError("%s.%s: %r must be true or false" % (path, name, value))
        flags[name] = value
    if flags["expect_events"] and not flags["writable"]:
        raise FamilyFileError(
            "%s.expect_events: a calendar that is not writable cannot receive pretend events (set writable: true too)" % path
        )
    backup = raw.get("backup", "ical")
    if backup not in _BACKUP_KINDS:
        raise FamilyFileError("%s.backup: %r must be one of %s" % (path, backup, ", ".join(_BACKUP_KINDS)))

    calendar = {
        "key": key,
        "calendar_id": calendar_id.strip(),
        "person": person,
        "writable": flags["writable"],
        "expect_events": flags["expect_events"],
        "backup": backup,
    }
    url = raw.get("ical_secret_url")
    if url is None:
        if backup == "ical":
            raise FamilyFileError(
                "%s.ical_secret_url: needed for backup: ical (Settings > Integrate calendar > Secret address in iCal "
                "format), or use backup: ha-snapshot for a calendar you do not own" % path
            )
    else:
        if not isinstance(url, str) or not url.startswith(_ICAL_URL_PREFIX):
            raise FamilyFileError("%s.ical_secret_url: must start with %s" % (path, _ICAL_URL_PREFIX))
        if not url.endswith(".ics"):
            raise FamilyFileError("%s.ical_secret_url: must end with .ics" % path)
        calendar["ical_secret_url"] = url
    return calendar


def _parse_google(raw: Any) -> Optional[dict]:
    """The google block: None when absent, else a normalised copy (calendars always a list).

    The person of each calendar is checked against the members once they are parsed.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise FamilyFileError("google: must be a mapping or null")
    _reject_unknown(raw, _GOOGLE_KEYS, "google")
    for name in ("client_id", "client_secret"):
        value = raw.get(name)
        if not isinstance(value, str) or not value.strip():
            raise FamilyFileError("google.%s: a non-empty text is needed" % name)
    raw_calendars = raw.get("calendars", [])
    if not isinstance(raw_calendars, list):
        raise FamilyFileError("google.calendars: must be a list")
    calendars = [_parse_google_calendar(item, index) for index, item in enumerate(raw_calendars)]
    seen_keys: dict[str, int] = {}
    seen_ids: dict[str, int] = {}
    for index, calendar in enumerate(calendars):
        if calendar["key"] in seen_keys:
            raise FamilyFileError(
                "google.calendars[%d].key: %r repeats google.calendars[%d]" % (index, calendar["key"], seen_keys[calendar["key"]])
            )
        seen_keys[calendar["key"]] = index
        if calendar["calendar_id"] in seen_ids:
            raise FamilyFileError(
                "google.calendars[%d].calendar_id: repeats google.calendars[%d]" % (index, seen_ids[calendar["calendar_id"]])
            )
        seen_ids[calendar["calendar_id"]] = index
    return {"client_id": raw["client_id"].strip(), "client_secret": raw["client_secret"].strip(), "calendars": calendars}


def _parse_member(raw: Any, index: int, google_keys: Optional[set[str]]) -> Member:
    path = "members[%d]" % index
    if not isinstance(raw, dict):
        raise FamilyFileError("%s: must be a mapping" % path)
    _reject_unknown(raw, _MEMBER_KEYS, path)

    name = raw.get("first_name")
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise FamilyFileError(
            "%s.first_name: %r must start with a letter and use only letters, spaces, apostrophes and hyphens (31 characters at most)"
            % (path, name)
        )
    role = raw.get("role")
    if role not in _ROLES:
        raise FamilyFileError("%s.role: %r must be one of %s" % (path, role, ", ".join(_ROLES)))
    admin = raw.get("admin", False)
    if not isinstance(admin, bool):
        raise FamilyFileError("%s.admin: %r must be true or false" % (path, admin))
    if admin and role != "parent":
        raise FamilyFileError("%s.admin: only a parent can be the admin" % path)

    age = raw.get("age")
    if role == "child":
        if isinstance(age, bool) or not isinstance(age, int):
            raise FamilyFileError("%s.age: a child needs a whole-number age (%d to %d)" % (path, _AGE_MIN, _AGE_MAX))
        if not _AGE_MIN <= age <= _AGE_MAX:
            raise FamilyFileError("%s.age: %d is outside %d to %d" % (path, age, _AGE_MIN, _AGE_MAX))
    elif age is not None:
        raise FamilyFileError("%s.age: a parent carries no age" % path)

    color = raw.get("color")
    if not isinstance(color, str) or not _COLOR_RE.match(color):
        raise FamilyFileError("%s.color: %r must look like #7ec9d9" % (path, color))

    calendar = raw.get("calendar", "local")
    if not isinstance(calendar, str):
        raise FamilyFileError("%s.calendar: %r must be \"local\" or \"google:<key>\"" % (path, calendar))
    if calendar != "local":
        if not calendar.startswith("google:") or len(calendar) == len("google:"):
            raise FamilyFileError("%s.calendar: %r must be \"local\" or \"google:<key>\"" % (path, calendar))
        if google_keys is None:
            raise FamilyFileError("%s.calendar: %r needs a google block (see dev/GOOGLE.md)" % (path, calendar))
        if calendar[len("google:"):] not in google_keys:
            raise FamilyFileError("%s.calendar: %r is not a key of the google block" % (path, calendar))

    return Member(
        first_name=name,
        username=username_for(name),
        role=role,
        admin=admin,
        age=age,
        color=color,
        calendar=calendar,
    )


def parse(data: Any, source: str = "") -> Family:
    """Validate parsed YAML and return the Family; raise FamilyFileError naming the key path."""
    if not isinstance(data, dict):
        raise FamilyFileError("file: the top level must be a mapping")
    _reject_unknown(data, _TOP_KEYS, "")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise FamilyFileError("schema_version: must be %d, found %r" % (SCHEMA_VERSION, data.get("schema_version")))

    google = _parse_google(data.get("google"))
    google_keys: Optional[set[str]] = {c.get("key") for c in google["calendars"] if isinstance(c, dict)} if google else None

    raw_members = data.get("members")
    if not isinstance(raw_members, list) or not raw_members:
        raise FamilyFileError("members: needs a non-empty list")
    members = tuple(_parse_member(raw, index, google_keys) for index, raw in enumerate(raw_members))
    if google:
        names = {member.first_name for member in members}
        for index, calendar in enumerate(google["calendars"]):
            if calendar["person"] not in names:
                raise FamilyFileError(
                    "google.calendars[%d].person: %r is not a member (members: %s)"
                    % (index, calendar["person"], ", ".join(sorted(names)))
                )

    seen_names: dict[str, int] = {}
    seen_users: dict[str, int] = {}
    for index, member in enumerate(members):
        lowered = member.first_name.lower()
        if lowered in seen_names:
            raise FamilyFileError(
                "members[%d].first_name: %r repeats members[%d] (names are compared ignoring case)"
                % (index, member.first_name, seen_names[lowered])
            )
        seen_names[lowered] = index
        if member.username == ADMIN_USERNAME:
            raise FamilyFileError(
                "members[%d].first_name: %r would use the tooling login %r" % (index, member.first_name, ADMIN_USERNAME)
            )
        if member.username in seen_users:
            raise FamilyFileError(
                "members[%d].first_name: login name %r repeats members[%d]"
                % (index, member.username, seen_users[member.username])
            )
        seen_users[member.username] = index

    admins = [i for i, m in enumerate(members) if m.admin]
    if len(admins) != 1:
        raise FamilyFileError("members: exactly one member needs admin: true (found %d)" % len(admins))
    if not any(m.role == "parent" and not m.admin for m in members):
        raise FamilyFileError("members: at least one parent other than the admin is needed (admin: false)")
    return Family(members=members, google=google, source=source)


def load(path: Optional[str] = None, say: Callable[[str], None] = print) -> Family:
    """Load the family file: ``path`` when given, else the local file, else the invented example."""
    import yaml  # PyYAML ships with Home Assistant; imported here so pure modules never need it

    if path:
        chosen = Path(path)
        if not chosen.is_file():
            raise FamilyFileError("file: %s does not exist" % path)
    elif LOCAL_FILE.is_file():
        chosen = LOCAL_FILE
    else:
        chosen = EXAMPLE_FILE
    say("family file: %s" % chosen)
    try:
        data = yaml.safe_load(chosen.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as err:
        raise FamilyFileError("file: %s cannot be read: %s" % (chosen, err)) from err
    return parse(data, source=str(chosen))
