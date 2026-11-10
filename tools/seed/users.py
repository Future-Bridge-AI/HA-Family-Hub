"""Home Assistant accounts for the family (D-13, D-27).

Every family-file member gets a login. The admin parent is in system-admin, everyone else in
system-users. Passwords (and each child's kiosk PIN) are generated once into the credentials file
and reused, so a reset hands back the same sign-in details.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from .client import HAWebSocket, SeedError
from .creds import CredentialStore
from .family_file import Family, Member

_LOGGER = logging.getLogger(__name__)

GROUP_ADMIN = "system-admin"
GROUP_USERS = "system-users"


def _group_ids(member: Member) -> list[str]:
    return [GROUP_ADMIN] if member.admin else [GROUP_USERS]


async def _list_users(ws: HAWebSocket) -> list[dict]:
    reply = await ws.call("config/auth/list")
    return [u for u in reply["result"] if not u.get("system_generated")]


def _find_existing(users: list[dict], member: Member) -> Optional[dict]:
    for user in users:
        if (user.get("username") or "").lower() == member.username:
            return user
    return None


async def ensure_users(
    ws: HAWebSocket, creds: CredentialStore, family: Family, say: Callable[[str], None] = print
) -> dict[str, str]:
    """Create any missing account and return ``first_name -> user id`` in file order."""
    users = await _list_users(ws)
    ids: dict[str, str] = {}
    created = 0
    for member in family.members:
        login = creds.member(member.first_name)
        if member.is_child:
            creds.pin(member.first_name)  # generated once, applied later through Family Hub
        existing = _find_existing(users, member)
        if existing is not None:
            groups = existing.get("group_ids") or []
            if groups != _group_ids(member):
                raise SeedError(
                    "users",
                    "account %r exists in groups %s but the family file needs %s; run the reset"
                    % (member.username, groups, _group_ids(member)),
                )
            ids[member.first_name] = existing["id"]
            continue
        reply = await ws.call(
            "config/auth/create", name=member.first_name, group_ids=_group_ids(member), local_only=False
        )
        user_id = reply["result"]["user"]["id"]
        try:
            await ws.call(
                "config/auth_provider/homeassistant/create",
                user_id=user_id,
                username=login["username"],
                password=login["password"],
            )
        except SeedError:
            # Do not leave a half-made account behind: the next run would not find it by login name.
            await ws.call("config/auth/delete", user_id=user_id)
            raise
        ids[member.first_name] = user_id
        created += 1
    say("users: %d accounts (%d created)" % (len(ids), created))
    return ids
