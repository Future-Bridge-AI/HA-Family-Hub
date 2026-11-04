"""Seeded content follows UI-SPEC S5 on any day: volumes, shapes and no overdue chores."""
from __future__ import annotations

import unittest
from collections import Counter
from datetime import date, timedelta

from tools.seed import family_file
from tools.seed.content import Content, build_content
from tools.seed.envs import ENVIRONMENTS
from tools.seed.family_file import EXAMPLE_FILE, Family, Member

# 14 consecutive days that include a Sunday (Feb 22 and Mar 1) and a month end (Feb 28).
START = date(2026, 2, 22)
DAYS = [START + timedelta(days=n) for n in range(14)]
DEV = ENVIRONMENTS["dev"]
PREVIEW = ENVIRONMENTS["preview"]


def example() -> Family:
    return family_file.load(str(EXAMPLE_FILE), lambda _line: None)


class ContentRulesTests(unittest.TestCase):
    def test_the_dates_cover_a_sunday_and_a_month_end(self) -> None:
        self.assertGreaterEqual(len(DAYS), 14)
        self.assertIn(6, {d.weekday() for d in DAYS})
        self.assertTrue(any((d + timedelta(days=1)).day == 1 for d in DAYS))

    def test_every_child_has_four_to_six_recurring_chores_with_two_due_today(self) -> None:
        family = example()
        for today in DAYS:
            content = build_content(family, DEV, today)
            for child in family.children:
                chores = [c for c in content.chores if c.assignee == child.first_name]
                with self.subTest(day=today.isoformat(), child=child.first_name):
                    self.assertTrue(4 <= len(chores) <= 6, len(chores))
                    due_today = [c for c in chores if c.due == today]
                    self.assertGreaterEqual(len(due_today), 2)
                    daily = [c for c in chores if c.recur_type == "interval" and c.recur_interval_days == 1]
                    self.assertGreaterEqual(len(daily), 2)
                    self.assertTrue(all(c.due >= today for c in chores), "an overdue chore")
                    for chore in chores:
                        self.assertTrue(chore.recur_type in ("interval", "weekdays"), chore)
                        self.assertEqual(chore.reminder_minutes, ())
                        self.assertTrue(chore.no_approval_required)
                        self.assertTrue(1 <= chore.star_value <= 5)
                        if chore.recur_type == "weekdays":
                            self.assertEqual(chore.recur_weekdays, (chore.due.weekday(),))
                            self.assertIn((chore.due - today).days, (0, 1))

    def test_five_rewards_and_every_balance_buys_the_cheapest_but_not_the_dearest(self) -> None:
        family = example()
        for today in DAYS:
            content = build_content(family, DEV, today)
            with self.subTest(day=today.isoformat()):
                self.assertEqual(sorted(r.cost_stars for r in content.rewards), [10, 15, 20, 25, 40])
                self.assertEqual(set(content.balances), {c.first_name for c in family.children})
                for balance in content.balances.values():
                    self.assertTrue(10 <= balance < 40, balance)

    def test_dinners_on_six_of_the_next_seven_nights(self) -> None:
        family = example()
        for today in DAYS:
            content = build_content(family, PREVIEW, today)
            days = [m.day for m in content.meals]
            with self.subTest(day=today.isoformat()):
                self.assertEqual(len(days), 6)
                self.assertEqual(len(set(days)), 6)
                window = {today + timedelta(days=n) for n in range(7)}
                self.assertTrue(set(days) <= window)
                self.assertEqual(len(window - set(days)), 1)
                self.assertTrue(all(m.block == 2 for m in content.meals))
                self.assertTrue(all(m.title for m in content.meals))

    def test_list_sizes_recipes_pantry_goal_and_routine(self) -> None:
        family = example()
        for today in DAYS:
            content = build_content(family, DEV, today)
            with self.subTest(day=today.isoformat()):
                sizes = Counter(item.list_name for item in content.items)
                self.assertEqual(sizes, Counter({"Groceries": 6, "Errands": 3, "Meal Suggestions": 1}))
                self.assertEqual(len(content.recipes), 3)
                for recipe in content.recipes:
                    self.assertTrue(3 <= len(recipe.steps) <= 5, recipe.name)
                    self.assertTrue(recipe.ingredients, recipe.name)
                self.assertEqual(len({r.uid for r in content.recipes}), 3)
                self.assertEqual(len(content.pantry), 3)
                self.assertIsNotNone(content.goal)
                self.assertEqual(content.goal.target_count, 5)
                self.assertEqual(content.goal.assignee, family.children[0].first_name)
                for child in family.children:
                    steps = [s for s in content.routines if s.member == child.first_name]
                    self.assertEqual(len(steps), 3)
                    self.assertTrue(all(s.category == "morning" for s in steps))

    def test_summaries_are_unique_within_each_list(self) -> None:
        content = build_content(example(), DEV, START)
        keys = [(i.list_name, i.summary) for i in content.items]
        self.assertEqual(len(keys), len(set(keys)))
        titles = [(c.assignee, c.title) for c in content.chores]
        self.assertEqual(len(titles), len(set(titles)))


class ContentDeterminismTests(unittest.TestCase):
    def test_same_inputs_give_equal_output_in_the_same_order(self) -> None:
        family = example()
        for today in DAYS:
            self.assertEqual(build_content(family, DEV, today), build_content(family, DEV, today))

    def test_dev_and_preview_share_the_same_week(self) -> None:
        family = example()
        self.assertEqual(build_content(family, DEV, START), build_content(family, PREVIEW, START))

    def test_one_member_family_builds_without_chores_rewards_or_balances(self) -> None:
        solo = Family(
            members=(
                Member(
                    first_name="Pat",
                    username="pat",
                    role="parent",
                    admin=True,
                    age=None,
                    color="#7ec9d9",
                    calendar="local",
                ),
            )
        )
        for today in DAYS:
            content = build_content(solo, DEV, today)
            with self.subTest(day=today.isoformat()):
                self.assertIsInstance(content, Content)
                self.assertEqual((content.chores, content.rewards, content.balances), ((), (), {}))
                self.assertIsNone(content.goal)
                self.assertEqual(content.routines, ())
                self.assertEqual(len(content.meals), 6)
                self.assertEqual(len(content.items), 10)
                self.assertEqual(len(content.recipes), 3)


if __name__ == "__main__":
    unittest.main()
