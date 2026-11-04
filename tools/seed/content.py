"""Her pretend week: the content the seed puts on every card, built from the family and today's date.

Pure: no I/O and no Home Assistant imports, so the volume and shape rules (UI-SPEC S5) are
unit-tested over many dates. ``build_content`` is deterministic: the same family, environment and
date always give the same content in the same order.
"""
from __future__ import annotations

import dataclasses
from datetime import date, timedelta
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
    star_value: int = 5  # a star-reward goal needs a positive value


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


# --- the pretend week ------------------------------------------------------------------------

CHORE_RECUR_INTERVAL = "interval"
CHORE_RECUR_WEEKDAYS = "weekdays"
ROUTINE_MORNING = "morning"
MEAL_BLOCK_DINNER = 2  # the card's default blocks are Breakfast, Lunch, Dinner

# (title, recurrence, days from today the chore is next due, stars); a child gets the first N.
# Daily chores are due today. A weekly chore repeats on the weekday it is first due, which is
# today or tomorrow, so nothing is overdue on the day it is seeded.
_CHORE_POOL: tuple[tuple[str, str, int, int], ...] = (
    ("Make your bed", CHORE_RECUR_INTERVAL, 0, 1),
    ("Feed the cat", CHORE_RECUR_INTERVAL, 0, 1),
    ("Set the table", CHORE_RECUR_WEEKDAYS, 0, 2),
    ("Tidy toys", CHORE_RECUR_WEEKDAYS, 1, 2),
    ("Take out the recycling", CHORE_RECUR_WEEKDAYS, 0, 3),
    ("Read for 15 minutes", CHORE_RECUR_WEEKDAYS, 1, 2),
)

_REWARDS: tuple[Reward, ...] = (
    Reward("Extra screen time, 30 minutes", 10),
    Reward("Choose the movie", 15),
    Reward("Stay up 30 minutes late", 20),
    Reward("Ice cream trip", 25),
    Reward("Pick a small toy", 40),
)
# Enough for the cheapest reward (10) and not for the dearest (40): both card states show.
STARTING_BALANCE = 18

_FRIDAY = 4
_FRIDAY_DINNER = "Pizza Friday"
_OTHER_DINNERS = (
    "Spaghetti night",
    "Tacos",
    "Pancakes for dinner",
    "Roast chicken",
    "Soup and bread",
    "Jacket potatoes",
)
_NO_DINNER_OFFSET = 3  # one night is blank on purpose

_ROUTINE_STEPS = ("Brush teeth", "Get dressed", "Pack school bag")

_ITEMS: tuple[ListItem, ...] = (
    ListItem("Groceries", "Milk"),
    ListItem("Groceries", "Bread"),
    ListItem("Groceries", "Bananas"),
    ListItem("Groceries", "Cheddar"),
    ListItem("Groceries", "Tomatoes"),
    ListItem("Groceries", "Eggs"),
    ListItem("Errands", "Post the parcel"),
    ListItem("Errands", "Return library books"),
    ListItem("Errands", "Collect the dry cleaning"),
    ListItem("Meal Suggestions", "Fish pie"),
)

_RECIPES: tuple[Recipe, ...] = (
    Recipe(
        "seed-spaghetti-bolognese",
        "Spaghetti bolognese",
        ("500 g beef mince", "1 onion", "2 cloves garlic", "400 g tinned tomatoes", "350 g spaghetti"),
        (
            "Fry the onion and garlic until soft.",
            "Add the mince and brown it.",
            "Stir in the tomatoes and simmer for 20 minutes.",
            "Boil the spaghetti and serve with the sauce.",
        ),
    ),
    Recipe(
        "seed-veggie-tacos",
        "Veggie tacos",
        ("8 taco shells", "1 tin black beans", "1 pepper", "1 avocado", "grated cheese"),
        (
            "Warm the beans with the chopped pepper.",
            "Heat the taco shells.",
            "Fill the shells and top with avocado and cheese.",
        ),
    ),
    Recipe(
        "seed-banana-pancakes",
        "Banana pancakes",
        ("2 ripe bananas", "2 eggs", "100 g flour", "200 ml milk"),
        (
            "Mash the bananas and whisk in the eggs.",
            "Mix in the flour and milk until smooth.",
            "Fry spoonfuls in a hot pan until golden on both sides.",
        ),
    ),
)

_PANTRY: tuple[PantryExtra, ...] = (
    PantryExtra("Rice", "1 large bag", "Cupboard", "Basmati"),
    PantryExtra("Pasta", "3 packets", "Cupboard", ""),
    PantryExtra("Tinned tomatoes", "6 tins", "Cupboard", "Chopped"),
)


def _chores_for(child_name: str, age: Optional[int], today: date) -> tuple[Chore, ...]:
    count = 4 if (age or 0) <= 7 else 5 if (age or 0) <= 10 else 6
    chores = []
    for title, recur, offset, stars in _CHORE_POOL[:count]:
        due = today + timedelta(days=offset)
        daily = recur == CHORE_RECUR_INTERVAL
        chores.append(
            Chore(
                title=title,
                assignee=child_name,
                star_value=stars,
                due=due,
                recur_type=recur,
                recur_interval_days=1 if daily else 0,
                recur_weekdays=() if daily else (due.weekday(),),
            )
        )
    return tuple(chores)


def _meals_for(today: date) -> tuple[Meal, ...]:
    others = iter(_OTHER_DINNERS)
    meals = []
    for offset in range(7):
        if offset == _NO_DINNER_OFFSET:
            continue
        day = today + timedelta(days=offset)
        title = _FRIDAY_DINNER if day.weekday() == _FRIDAY else next(others)
        meals.append(Meal(title=title, day=day, block=MEAL_BLOCK_DINNER))
    return tuple(meals)


def build_content(family: Family, env: Env, today: date) -> Content:
    """Build the week for ``family`` as seen on ``today``.

    ``env`` is accepted so any environment-specific wording lives here; Dev and Preview currently
    show the same week. A family with no children has no chores, rewards, balances, goal or
    routines, but meals, lists, recipes and pantry notes are still there.
    """
    children = family.children
    chores = tuple(c for child in children for c in _chores_for(child.first_name, child.age, today))
    routines = tuple(
        RoutineStep(member=child.first_name, category=ROUTINE_MORNING, title=title)
        for child in children
        for title in _ROUTINE_STEPS
    )
    goal = Goal("Tidy room 5 days in a row", children[0].first_name, 5) if children else None
    return Content(
        chores=chores,
        rewards=_REWARDS if children else (),
        balances={child.first_name: STARTING_BALANCE for child in children},
        goal=goal,
        routines=routines,
        recipes=_RECIPES,
        meals=_meals_for(today),
        items=_ITEMS,
        pantry=_PANTRY,
    )
