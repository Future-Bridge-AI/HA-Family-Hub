"""The environment table: the single place that says what Dev and Preview are.

Every tool keys on ENVIRONMENTS instead of scattered "is this Preview" checks. "home" is never
a target: the family's real Home Assistant has no entry here, so nothing in tools/ can be
pointed at it by naming it.

The base URL guard also lives here: a seed run only ever talks to a loopback address, and the
refusal happens before any socket is opened.
"""
from __future__ import annotations

import dataclasses
from typing import Optional
from urllib.parse import urlparse

LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


class GuardRefused(Exception):
    """A safety guard refused the request before anything was sent (exit code 2)."""

    exit_code = 2


@dataclasses.dataclass(frozen=True)
class Env:
    """One non-production environment."""

    key: str
    location_name: str
    port: int
    compose_project: str
    config_dir: str
    tag: str
    marker_prefix: str
    theme: str
    stamp_word: str
    dashboard_title: str


ENVIRONMENTS: dict[str, Env] = {
    "dev": Env(
        key="dev",
        location_name="Family Hub DEV",
        port=8130,
        compose_project="familyhub-dev",
        config_dir="dev/.ha-dev",
        tag="[DEV] ",
        marker_prefix="family-hub-seed:dev:",
        theme="blossom",
        stamp_word="Dev",
        dashboard_title="Family Hub DEV",
    ),
    "preview": Env(
        key="preview",
        location_name="Family Hub PREVIEW",
        port=8124,
        compose_project="familyhub-preview",
        config_dir="dev/.ha-preview",
        tag="[PREVIEW] ",
        marker_prefix="family-hub-seed:preview:",
        theme="midnight",
        stamp_word="Preview",
        dashboard_title="Family Hub PREVIEW",
    ),
}


def get_env(key: str) -> Env:
    """Return the environment named ``key`` or refuse (only dev and preview exist)."""
    try:
        return ENVIRONMENTS[key]
    except KeyError:
        raise GuardRefused(
            "unknown target %r: only %s can be a seed target"
            % (key, " and ".join(sorted(ENVIRONMENTS)))
        ) from None


def base_url(env: Env, override: Optional[str] = None) -> str:
    """Return the HTTPS base URL for ``env``; an override must be https on a loopback host."""
    if override is None:
        return "https://127.0.0.1:%d" % env.port
    try:
        parts = urlparse(override)
        host = parts.hostname
        parts.port  # noqa: B018 - raises ValueError for a malformed port
    except ValueError:
        raise GuardRefused("refusing %r: not a valid URL; only a loopback address is allowed" % override) from None
    if parts.scheme != "https":
        raise GuardRefused(
            "refusing %r: the seed tool only talks https to a loopback address" % override
        )
    if parts.username is not None or parts.password is not None:
        raise GuardRefused("refusing %r: credentials in the URL are not allowed" % override)
    if host not in LOOPBACK_HOSTS:
        raise GuardRefused(
            "refusing %r: %r is not a loopback address (allowed: %s)"
            % (override, host, ", ".join(LOOPBACK_HOSTS))
        )
    return override.rstrip("/")
