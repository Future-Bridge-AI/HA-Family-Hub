"""Back up every chosen Google calendar before anything destructive runs (D-08, D-30).

Placeholder for the failing tests (plan 02-08, task 3): replaced by the real implementation next.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


class BackupError(Exception):
    """A backup failed; nothing may be stopped, wiped or deleted (exit code 5)."""

    exit_code = 5


def default_fetch(url: str) -> tuple[int, str]:
    raise NotImplementedError


def backup_calendars(family: Any, env: Any, out_root: str, now: Any, fetch: Optional[Callable] = None, snapshot: Optional[Callable] = None) -> str:
    return ""
