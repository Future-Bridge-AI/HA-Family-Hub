"""Her pretend week: the content the seed puts on every card, built from the family and today's date.

Pure: no I/O and no Home Assistant imports, so the volume and shape rules (UI-SPEC S5) are
unit-tested over many dates. ``build_content`` is deterministic: the same family, environment and
date always give the same content in the same order.
"""
from __future__ import annotations

import dataclasses
from datetime import date
from typing import Optional

from .envs import Env
from .family_file import Family


@dataclasses.dataclass(frozen=True)
class Chore:
    title: str
    assignee: str
    star_value: int
    due: date
    recur_type: str
    recur_interval_days: int = 0
    recur_weekdays: tuple[int, ...] = ()
    no_approval_required: bool = True
    reminder_minutes: tuple[int, ...] = ()


@dataclasses.dataclass(frozen=True)
class Reward:
    title: str
    cost_stars: int


@dataclasses.dataclass(frozen=True)
class Meal:
    title: str
    day: date
    block: int = 2


@dataclasses.dataclass(frozen=True)
class ListItem:
    list_name: str
    summary: str


@dataclasses.dataclass(frozen=True)
class Recipe:
    uid: str
    name: str
    ingredients: tuple[str, ...]
    steps: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class RoutineStep:
    member: str
    category: str
    title: str


@dataclasses.dataclass(frozen=True)
class Goal:
    title: str
    assignee: str
    target_count: int


@dataclasses.dataclass(frozen=True)
class PantryExtra:
    name: str
    quantity: str
    location: str
    notes: str


@dataclasses.dataclass(frozen=True)
class Content:
    chores: tuple[Chore, ...] = ()
    rewards: tuple[Reward, ...] = ()
    balances: dict = dataclasses.field(default_factory=dict)
    goal: Optional[Goal] = None
    routines: tuple[RoutineStep, ...] = ()
    recipes: tuple[Recipe, ...] = ()
    meals: tuple[Meal, ...] = ()
    items: tuple[ListItem, ...] = ()
    pantry: tuple[PantryExtra, ...] = ()


def build_content(family: Family, env: Env, today: date) -> Content:
    return Content()
