"""resources-sync (RED stub): every function returns an empty answer so the tests fail on behaviour."""
from __future__ import annotations

from typing import Any, Callable, Optional


def served_js_files(integration_dir: str) -> dict[str, str]:
    return {}


def served_urls(integration_dir: str) -> dict[str, str]:
    return {}


def content_hash(path: str) -> str:
    return ""


def plan_updates(
    resources: list[dict], files: dict[str, str], urls: Optional[dict[str, str]] = None
) -> list[dict]:
    return []


async def sync(
    client: Any, token: str, integration_dir: str, apply: bool = True, say: Callable[[str], None] = print
) -> dict:
    return {"updated": 0, "created": 0, "unchanged": 0}
