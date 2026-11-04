"""Bring a fresh Home Assistant up as a named, HTTPS, onboarded Dev or Preview.

Steps (each prints one line through ``say``):

1. wait_http          poll until HA answers over TLS (verified against the local CA)
2. onboard_if_needed  create the tool's admin and finish onboarding, only while it is open
3. wait_running       WebSocket get_config until state is RUNNING
4. identity guard     an instance this run did not onboard must already carry the target's name
5. promote_http       the http: YAML is only a *pending* config and reverts after five minutes
                      unless promoted (Pitfall 1)
6. apply_core_config  location_name plus the host values (TZ and HA_* variables, D-31)

Nothing here writes to an instance before the identity guard has passed.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .client import HAClient, HAWebSocket, SeedError
from .creds import CredentialStore
from .envs import Env

_LOGGER = logging.getLogger(__name__)

Say = Callable[[str], None]

# Onboarding steps that need the admin's token, in the order HA expects them.
_TOKEN_STEPS = ("core_config", "analytics", "integration")


@dataclass
class OnboardResult:
    """What onboard_if_needed did: ``onboarded`` is True when this run found onboarding open."""

    onboarded: bool
    token: Optional[str] = None


def host_core_settings(environ: Optional[dict[str, str]] = None) -> dict[str, object]:
    """Map the TZ and HA_* host variables to config/core/update fields (only those set)."""
    env = os.environ if environ is None else environ
    settings: dict[str, object] = {}
    plain = (
        ("TZ", "time_zone"),
        ("HA_COUNTRY", "country"),
        ("HA_CURRENCY", "currency"),
        ("HA_UNIT_SYSTEM", "unit_system"),
        ("HA_LANGUAGE", "language"),
    )
    for var, field in plain:
        if env.get(var):
            settings[field] = env[var]
    for var, field, cast in (
        ("HA_LATITUDE", "latitude", float),
        ("HA_LONGITUDE", "longitude", float),
        ("HA_ELEVATION", "elevation", int),
    ):
        if env.get(var):
            try:
                settings[field] = cast(env[var])
            except ValueError:
                raise SeedError("config", "%s=%r is not a valid number" % (var, env[var])) from None
    return settings


async def wait_http(client: HAClient, timeout: float, say: Say) -> None:
    """Poll GET /api/onboarding until HA answers; a TLS failure is fatal at once."""
    deadline = time.monotonic() + timeout
    announced = False
    while True:
        try:
            await client.rest("GET", "/api/onboarding")
            say("home assistant answers at %s" % client.base_url)
            return
        except SeedError as err:
            if err.code != "connect":
                raise
            if time.monotonic() >= deadline:
                raise SeedError(
                    "timeout",
                    "no answer from %s within %d s (last error: %s)"
                    % (client.base_url, int(timeout), err.message),
                ) from err
            if not announced:
                say("waiting for home assistant at %s" % client.base_url)
                announced = True
            await asyncio.sleep(2)


async def _onboarding_status(client: HAClient, settle: float) -> Optional[dict[str, bool]]:
    """Return {step: done}, or None once HA no longer serves the onboarding API (404).

    ``settle`` keeps asking for a while when the answer is 404 or 5xx, because the onboarding
    views are registered a moment after the HTTP server starts listening.
    """
    deadline = time.monotonic() + settle
    while True:
        status, body = await client.rest("GET", "/api/onboarding")
        if status == 200 and isinstance(body, list):
            return {item["step"]: bool(item["done"]) for item in body}
        if status in (404, 502, 503) and time.monotonic() < deadline:
            await asyncio.sleep(1)
            continue
        if status == 404:
            return None
        raise SeedError("http", "unexpected answer from /api/onboarding: HTTP %s" % status)


async def onboard_if_needed(
    client: HAClient, creds: CredentialStore, language: str, say: Say
) -> OnboardResult:
    """Finish onboarding while it is open; do nothing on an onboarded instance."""
    # A brand new tool (no stored password yet) has never onboarded anything, so a 404 right
    # after start is more likely "views not registered yet" than "already onboarded".
    steps = await _onboarding_status(client, settle=0.0 if creds.exists() else 30.0)
    if steps is None and creds.exists():
        # Right after a reset the stored credentials outlive the wiped instance, and its 404 looks
        # like "already onboarded" until the onboarding views are registered. Only a login that
        # works proves it is onboarded; if it does not, keep asking for the onboarding steps.
        stored = creds.admin()
        try:
            await client.login(stored["username"], stored["password"])
        except SeedError as err:
            if err.code != "auth":
                raise
            steps = await _onboarding_status(client, settle=30.0)
    if steps is None or all(steps.values()):
        return OnboardResult(onboarded=False)

    admin = creds.admin()
    token: Optional[str] = None
    if not steps.get("user"):
        status, body = await client.rest(
            "POST",
            "/api/onboarding/users",
            json={
                "client_id": client.client_id,
                "name": "Family Hub tools",
                "username": admin["username"],
                "password": admin["password"],
                "language": language,
            },
        )
        if status != 200 or not isinstance(body, dict) or "auth_code" not in body:
            raise SeedError("onboarding", "creating the admin failed (HTTP %s): %s" % (status, body))
        token = await client.exchange_code(body["auth_code"])
        say("onboarded")
    else:
        # An earlier run created the admin and stopped before the last steps.
        token = await client.login(admin["username"], admin["password"])
        say("onboarding resumed")

    for step in _TOKEN_STEPS:
        if steps.get(step):
            continue
        payload: dict = {}
        if step == "integration":
            payload = {
                "client_id": client.client_id,
                "redirect_uri": client.client_id + "?auth_callback=1",
            }
        status, body = await client.rest(
            "POST", "/api/onboarding/%s" % step, json=payload, token=token
        )
        if status != 200:
            raise SeedError("onboarding", "onboarding step %s failed (HTTP %s): %s" % (step, status, body))
    return OnboardResult(onboarded=True, token=token)


async def wait_running(ws: HAWebSocket, timeout: float, say: Say) -> dict:
    """Poll WebSocket get_config until state is RUNNING and return the config."""
    deadline = time.monotonic() + timeout
    while True:
        config = (await ws.call("get_config"))["result"]
        if config.get("state") == "RUNNING":
            return config
        if time.monotonic() >= deadline:
            raise SeedError(
                "timeout", "home assistant did not reach RUNNING (state %s)" % config.get("state")
            )
        await asyncio.sleep(2)


def check_identity(config: dict, env: Env, fresh: bool) -> None:
    """Refuse to write to an onboarded instance that is not the target.

    ``fresh`` means this run found onboarding still open, so the instance is a brand new one
    that still has the default name.
    """
    if fresh:
        return
    actual = config.get("location_name")
    if actual != env.location_name:
        raise SeedError(
            "identity",
            "refusing to write: this instance is named %r but target %r expects %r"
            % (actual, env.key, env.location_name),
        )


async def promote_http(ws: HAWebSocket, say: Say) -> None:
    """Promote a pending HTTP config to stable and assert it stuck."""
    http = (await ws.call("http/config"))["result"]
    if http.get("active_config_type") == "pending":
        await ws.call("http/config/promote")
        say("http config promoted")
        http = (await ws.call("http/config"))["result"]
    if http.get("active_config_type") != "stable" or http.get("revert_at") is not None:
        raise SeedError(
            "http_config",
            "http config is not stable after promotion (active %s, revert_at %s)"
            % (http.get("active_config_type"), http.get("revert_at")),
        )


async def apply_core_config(ws: HAWebSocket, env: Env, say: Say) -> None:
    """Set the environment's name and the host's core settings."""
    fields = dict(host_core_settings())
    await ws.call("config/core/update", location_name=env.location_name, **fields)
    say("location_name = %s" % env.location_name)


async def open_admin(client: HAClient, env: Env, creds: CredentialStore) -> tuple[str, HAWebSocket]:
    """Log in as the tool's admin on an already onboarded instance, after the identity guard.

    Every command that writes to an existing instance starts here, so the location_name check
    happens before its first write.
    """
    if not creds.exists():
        raise SeedError(
            "auth",
            "no credentials for target %s in %s: run bootstrap first" % (env.key, creds.path),
        )
    admin = creds.admin()
    token = await client.login(admin["username"], admin["password"])
    ws = await client.ws(token)
    config = (await ws.call("get_config"))["result"]
    check_identity(config, env, fresh=False)
    return token, ws


async def bootstrap(
    client: HAClient, env: Env, creds: CredentialStore, timeout: float, say: Say
) -> HAWebSocket:
    """Run every bootstrap step and return the admin's open WebSocket for later steps."""
    await wait_http(client, timeout, say)
    language = os.environ.get("HA_LANGUAGE") or "en"
    result = await onboard_if_needed(client, creds, language, say)
    token = result.token
    if token is None:
        if not creds.exists():
            raise SeedError(
                "auth",
                "%s is already onboarded and %s holds no credentials for target %s"
                % (client.base_url, creds.path, env.key),
            )
        admin = creds.admin()
        token = await client.login(admin["username"], admin["password"])
    ws = await client.ws(token)
    config = await wait_running(ws, timeout, say)
    check_identity(config, env, fresh=result.onboarded)
    await promote_http(ws, say)
    await apply_core_config(ws, env, say)
    return ws
