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
        if not google_keys:
            raise FamilyFileError(
                "%s.calendar: %r needs a google block, which needs plan 02-08 (use \"local\" until then)"
                % (path, calendar)
            )
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

    google = data.get("google")
    if google is not None:
        # The google block is defined by plan 02-08; until then a non-null block cannot be honoured.
        raise FamilyFileError("google: the google block needs plan 02-08 (set it to null until then)")
    google_keys: Optional[set[str]] = None

    raw_members = data.get("members")
    if not isinstance(raw_members, list) or not raw_members:
        raise FamilyFileError("members: needs a non-empty list")
    members = tuple(_parse_member(raw, index, google_keys) for index, raw in enumerate(raw_members))

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
    return Family(members=members, google=None, source=source)


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
