"""Stub: replaced by the real checks in the next commit."""
from __future__ import annotations

from typing import Any

from .envs import Env

ALLOWED_ENTRY_DOMAINS: tuple[str, ...] = ()


def check_identity(location_name: Any, env: Env, theme_id: Any, dashboard_title: Any) -> list[str]:
    return []


def check_isolation(settings: Any, entities: Any, entry_domains: Any, components: Any) -> list[str]:
    return []


def check_grocy(reply: Any) -> list[str]:
    return []


def check_dashboard(entry: Any, config: Any, env: Env) -> list[str]:
    return []


def check_sidebar(member: str, panels: Any, sidebar: Any, core: Any) -> list[str]:
    return []


def check_content(counts: Any) -> list[str]:
    return []
