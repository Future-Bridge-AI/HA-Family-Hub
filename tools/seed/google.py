"""The Google Calendar connection of Dev and Preview (D-07, D-10, D-15).

Home Assistant keeps a Google sign-in in two places: the application credential (the OAuth client the
developer made in his own Google Cloud project) and the config entry in ``.storage/core.config_entries``
(which holds the refresh token). A reset wipes both, and signing in again each time would make the
guardrail useless, so:

1. before the wipe the stopped instance's Google config entry is copied to
   ``<secrets-dir>/google-<env>.json`` (0600, outside the Home Assistant volume);
2. after the wipe, before Home Assistant starts, that entry is written back as the only entry of
   ``.storage/core.config_entries``;
3. once Home Assistant is up the seed creates the application credential from the family file and
   reloads the entry until it reports "loaded".

Without the credential the restored entry cannot load (Pitfall 7), and a missing sign-in is reported as
one plain instruction, never as a half-seeded instance.
"""
from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
import os
import time
from typing import Any, Awaitable, Callable, Optional

from .client import HAClient, HAWebSocket, SeedError

_LOGGER = logging.getLogger(__name__)

Say = Callable[[str], None]

DOMAIN = "google"
SIGNIN_CODE = "google_signin"
SIGNIN_HELP = "Google sign-in is needed once for this environment: see dev/GOOGLE.md, First sign-in, then re-run"

# How long a reloaded entry gets to reach "loaded" before the seed gives up on it.
LINK_TIMEOUT = 120.0

# Entry states that will not turn into "loaded" by waiting.
_FINAL_BAD_STATES = ("setup_error", "migration_error", "failed_unload")


def _env_key(env: Any) -> str:
    return env if isinstance(env, str) else env.key


def secret_path(secrets_dir: str, env: Any) -> str:
    """Where the saved Google entry of one environment lives."""
    return os.path.join(secrets_dir, "google-%s.json" % _env_key(env))


def _write_private(path: str, text: str) -> None:
    """Write ``text`` to ``path`` with mode 0600 inside a 0700 directory (never world readable)."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(fd, 0o600)
        handle.write(text)
    os.replace(tmp, path)


def save_entry(core_config_entries_json: str, secrets_dir: str, env: Any, say: Say = print) -> bool:
    """Save the Google config entry of a STOPPED instance; return True when one was written.

    ``core_config_entries_json`` is the text of ``.storage/core.config_entries``. Exactly one Google
    entry is expected. With none, nothing is changed (an older saved copy stays as it is) and the
    function says so.
    """
    try:
        document = json.loads(core_config_entries_json)
        entries = document["data"]["entries"]
    except (ValueError, KeyError, TypeError) as err:
        raise SeedError("google_save", "core.config_entries is not a config entries file: %s" % err) from err
    if not isinstance(entries, list):
        raise SeedError("google_save", "core.config_entries has no entries list")
    google = [entry for entry in entries if isinstance(entry, dict) and entry.get("domain") == DOMAIN]
    if not google:
        say("google: no entry to save")
        return False
    if len(google) > 1:
        raise SeedError(
            "google_save",
            "found %d Google entries; the seed keeps exactly one per environment (remove the others)" % len(google),
        )
    saved = {
        "version": document.get("version"),
        "minor_version": document.get("minor_version"),
        "entry": google[0],
    }
    _write_private(secret_path(secrets_dir, env), json.dumps(saved, indent=2, sort_keys=True) + "\n")
    say("google: entry saved to %s" % secret_path(secrets_dir, env))
    return True


def restore_entry(secrets_dir: str, env: Any) -> Optional[str]:
    """The text of a ``core.config_entries`` holding only the saved Google entry, or None."""
    path = secret_path(secrets_dir, env)
    try:
        with open(path, encoding="utf-8") as handle:
            saved = json.load(handle)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as err:
        raise SeedError("google_restore", "%s cannot be read: %s" % (path, err)) from err
    try:
        document = {
            "version": saved["version"],
            "minor_version": saved["minor_version"],
            "key": "core.config_entries",
            "data": {"entries": [saved["entry"]]},
        }
    except (KeyError, TypeError) as err:
        raise SeedError("google_restore", "%s is not a saved Google entry: %s" % (path, err)) from err
    return json.dumps(document, indent=2) + "\n"


async def ensure_credential(
    ws: HAWebSocket,
    google_block: dict,
    env: Any,
    load_component: Optional[Callable[[], Awaitable[None]]] = None,
    say: Say = print,
) -> str:
    """Create the Google application credential from the family file unless it exists; "created"/"present".

    The credential id Home Assistant derives is ``google.<client id>`` and the sign-in entry points at
    it, so the client id in the family file must not change between sign-in and reset.
    """
    try:
        listed = (await ws.call("application_credentials/list"))["result"]
    except SeedError as err:
        if err.code != "unknown_command" or load_component is None:
            raise
        # The component is only loaded once a Google entry or flow exists; starting (and refusing)
        # a Google flow loads it.
        await load_component()
        listed = (await ws.call("application_credentials/list"))["result"]
    client_id = google_block["client_id"]
    for item in listed:
        if item.get("domain") == DOMAIN and item.get("client_id") == client_id:
            say("google: application credential present")
            return "present"
    await ws.call(
        "application_credentials/create",
        domain=DOMAIN,
        client_id=client_id,
        client_secret=google_block["client_secret"],
        name="Family Hub %s" % _env_key(env),
    )
    say("google: application credential created")
    return "created"


async def _google_entries(client: HAClient, token: str) -> list[dict]:
    status, body = await client.rest("GET", "/api/config/config_entries/entry?domain=%s" % DOMAIN, token=token)
    if status != 200 or not isinstance(body, list):
        raise SeedError("http", "listing the Google config entries failed (HTTP %s): %s" % (status, body))
    return body


def _signin_error(state: str, reason: Optional[str] = None) -> SeedError:
    detail = "entry state: %s" % state
    if reason:
        detail += ", %s" % reason
    return SeedError(SIGNIN_CODE, "%s (%s)" % (SIGNIN_HELP, detail))


async def _reauth_pending(ws: HAWebSocket, entry_id: str) -> bool:
    """True when Home Assistant is waiting for the account to be linked again (a reauth flow)."""
    progress = (await ws.call("config_entries/flow/progress"))["result"]
    for flow in progress:
        context = flow.get("context") or {}
        if context.get("source") == "reauth" and context.get("entry_id") == entry_id:
            return True
    return False


async def _load_component(client: HAClient, token: str) -> None:
    """Start a Google config flow, which makes Home Assistant load the application_credentials component."""
    status, step = await client.rest(
        "POST",
        "/api/config/config_entries/flow",
        json={"handler": DOMAIN, "show_advanced_options": False},
        token=token,
    )
    flow_id = step.get("flow_id") if isinstance(step, dict) else None
    if flow_id:  # a form was shown: close it, nothing was entered
        await client.rest("DELETE", "/api/config/config_entries/flow/%s" % flow_id, token=token)


async def link(
    client: HAClient,
    token: str,
    ws: HAWebSocket,
    google_block: dict,
    env: Any,
    say: Say = print,
    timeout: float = LINK_TIMEOUT,
    reload: bool = True,
) -> dict:
    """Make the Google entry usable: credential, then reload (or just check) until it is "loaded".

    Raises SeedError ``google_signin`` with the one-time sign-in instruction when there is no entry
    yet, or when the entry sits in setup_error (or setup_retry with a reauth pending): the credential
    is missing or wrong, or the token was revoked or expired.
    """

    async def load_component() -> None:
        await _load_component(client, token)

    await ensure_credential(ws, google_block, env, load_component, say)
    entries = await _google_entries(client, token)
    if not entries:
        raise SeedError(SIGNIN_CODE, SIGNIN_HELP + " (no Google entry exists yet)")
    if len(entries) > 1:
        raise SeedError("google_entry", "found %d Google entries; the seed expects exactly one" % len(entries))
    entry = entries[0]
    entry_id = entry["entry_id"]
    if reload:
        status, body = await client.rest(
            "POST", "/api/config/config_entries/entry/%s/reload" % entry_id, token=token
        )
        if status != 200:
            _LOGGER.debug("reload of %s answered HTTP %s: %s", entry_id, status, body)
    deadline = time.monotonic() + timeout
    while True:
        entry = next((e for e in await _google_entries(client, token) if e["entry_id"] == entry_id), None)
        if entry is None:
            raise SeedError("google_entry", "the Google entry %s disappeared" % entry_id)
        state = entry.get("state")
        if state == "loaded":
            say("google: entry %s loaded" % entry_id)
            return entry
        if state in _FINAL_BAD_STATES:
            raise _signin_error(state, entry.get("reason"))
        if state == "setup_retry" and await _reauth_pending(ws, entry_id):
            raise _signin_error(state, entry.get("reason"))
        if time.monotonic() >= deadline:
            raise _signin_error(str(state), entry.get("reason"))
        await asyncio.sleep(1)


@dataclasses.dataclass
class Selection:
    """What the calendar selection changes: entity ids to keep, disable and enable, and chosen ids with no entity."""

    keep: list = dataclasses.field(default_factory=list)
    disable: list = dataclasses.field(default_factory=list)
    enable: list = dataclasses.field(default_factory=list)
    missing: list = dataclasses.field(default_factory=list)


def select_entities(registry: list, entry_unique_id: str, chosen_ids: list, entry_id: Optional[str] = None) -> Selection:
    return Selection()


def google_slots(family: Any, entity_map: dict) -> list:
    return []


def member_calendars(family: Any, entity_map: dict) -> dict:
    return {}
