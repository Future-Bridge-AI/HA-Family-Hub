"""The S5 week plan and the create/delete/keep diff, as pure tests (no Home Assistant)."""
from __future__ import annotations

import argparse
import datetime
import re
import unittest
from collections import defaultdict

from tools.seed import calendar_tags, events
from tools.seed.envs import ENVIRONMENTS
from tools.seed.events import CalendarSlot, DesiredEvent

DEV = ENVIRONMENTS["dev"]
PREVIEW = ENVIRONMENTS["preview"]
FAMILY = [CalendarSlot(name, "calendar." + name.lower()) for name in ("Sam", "Jordan", "Riley", "Casey")]
ALLOWED = frozenset(slot.entity_id for slot in FAMILY)
# 21 consecutive days starting on a Sunday: crosses the Monday rollovers of 2 and 9 and 16 November.
DATES = [datetime.date(2026, 11, 1) + datetime.timedelta(days=n) for n in range(21)]
KEY_SHAPE = re.compile(r"\d{4}w\d{2}-[1-7]-\d+-[a-z0-9]+")


def week_days(today: datetime.date, week: int) -> list[datetime.date]:
    monday = events.monday_of(today) + datetime.timedelta(days=7 * week)
    return [monday + datetime.timedelta(days=n) for n in range(7)]


def by_day(plan: list[DesiredEvent]) -> dict[datetime.date, list[DesiredEvent]]:
    grouped: dict[datetime.date, list[DesiredEvent]] = defaultdict(list)
    for item in plan:
        grouped[item.start.date()].append(item)
    return grouped


def unique_events(items: list[DesiredEvent]) -> set:
    """Events as a person sees them: a shared event on two calendars counts once."""
    return {(item.start, item.summary) for item in items}


def day_of(value) -> datetime.date:
    return value.date() if isinstance(value, datetime.datetime) else value


def to_raw(item: DesiredEvent, uid: str = "", **changes) -> dict:
    """The event as HA's GET /api/calendars would return it."""
    if item.all_day:
        start = {"date": item.start.date().isoformat()}
        end = {"date": item.end.date().isoformat()}
    else:
        start = {"dateTime": item.start.isoformat() + "+00:00"}
        end = {"dateTime": item.end.isoformat() + "+00:00"}
    raw = {
        "summary": item.summary,
        "description": item.description,
        "start": start,
        "end": end,
        "uid": uid or "uid-%s-%s" % (item.entity_id, item.key),
        "recurrence_id": None,
        "rrule": None,
    }
    raw.update(changes)
    return raw


def existing_of(plan: list[DesiredEvent]) -> dict[str, list[dict]]:
    existing: dict[str, list[dict]] = {slot.entity_id: [] for slot in FAMILY}
    for item in plan:
        existing[item.entity_id].append(to_raw(item))
    return existing


TODAY = datetime.date(2026, 11, 4)  # a Wednesday


class WindowTests(unittest.TestCase):
    def test_window_is_monday_to_monday_after_next_for_every_weekday(self) -> None:
        for today in DATES:
            start, end = events.window(today)
            self.assertEqual(start.weekday(), 0)
            self.assertEqual(start.date(), today - datetime.timedelta(days=today.weekday()))
            self.assertEqual(end - start, datetime.timedelta(days=14))

    def test_on_a_sunday_the_window_still_includes_the_following_week(self) -> None:
        sunday = datetime.date(2026, 11, 8)
        start, end = events.window(sunday)
        self.assertEqual(start.date(), datetime.date(2026, 11, 2))
        self.assertEqual(end.date(), datetime.date(2026, 11, 16))
        plan = events.plan_week_events(FAMILY, DEV, sunday)
        self.assertTrue(any(item.start.date() == datetime.date(2026, 11, 14) for item in plan))

    def test_delete_window_reaches_four_weeks_back_and_ends_with_the_plan_window(self) -> None:
        start, end = events.window(TODAY)
        dstart, dend = events.delete_window(TODAY)
        self.assertEqual(start - dstart, datetime.timedelta(days=28))
        self.assertEqual(end, dend)

    def test_window_is_half_open_event_at_window_end_is_outside(self) -> None:
        _start, end = events.window(TODAY)
        plan = events.plan_week_events(FAMILY, DEV, TODAY)
        self.assertTrue(all(item.start < end for item in plan))
        at_end = to_raw(plan[0], start={"dateTime": end.isoformat()})
        self.assertFalse(calendar_tags.matches(at_end, DEV, plan[0].entity_id, ALLOWED, *events.delete_window(TODAY)))


class PlanShapeTests(unittest.TestCase):
    def test_every_this_week_day_has_a_morning_or_all_day_and_an_evening_event(self) -> None:
        for today in DATES:
            grouped = by_day(events.plan_week_events(FAMILY, DEV, today))
            for day in week_days(today, 0):
                items = grouped[day]
                self.assertTrue(any(i.all_day or i.start.hour < 12 for i in items), (today, day))
                self.assertTrue(any(i.start.hour >= 16 and not i.all_day for i in items), (today, day))

    def test_saturday_has_four_events_and_friday_has_an_all_day_event(self) -> None:
        for today in DATES:
            grouped = by_day(events.plan_week_events(FAMILY, DEV, today))
            days = week_days(today, 0)
            self.assertEqual(len(unique_events(grouped[days[5]])), 4, today)
            self.assertTrue(any(i.all_day for i in grouped[days[4]]), today)

    def test_one_event_is_shared_by_two_calendars_with_the_same_key(self) -> None:
        for today in DATES:
            for week in (0, 1):
                days = set(week_days(today, week))
                plan = [i for i in events.plan_week_events(FAMILY, DEV, today) if i.start.date() in days]
                keys = defaultdict(list)
                for item in plan:
                    keys[item.key].append(item.entity_id)
                shared = {k: v for k, v in keys.items() if len(v) > 1}
                self.assertEqual(len(shared), 1, (today, week, shared))
                (entities,) = shared.values()
                self.assertEqual(len(set(entities)), 2)
                self.assertIn("Family movie night", [i.summary for i in plan if i.key in shared][0])

    def test_every_this_week_day_leaves_a_member_without_events(self) -> None:
        for today in DATES:
            grouped = by_day(events.plan_week_events(FAMILY, DEV, today))
            for day in week_days(today, 0):
                busy = {i.entity_id for i in grouped[day]}
                self.assertLess(len(busy), len(FAMILY), (today, day, busy))

    def test_next_week_sunday_is_empty_and_next_week_tuesday_has_one_event(self) -> None:
        for today in DATES:
            grouped = by_day(events.plan_week_events(FAMILY, DEV, today))
            days = week_days(today, 1)
            self.assertEqual(len(grouped[days[6]]), 0, today)
            self.assertEqual(len(unique_events(grouped[days[1]])), 1, today)

    def test_zero_one_many_populated_all_hold_in_the_window(self) -> None:
        for today in DATES:
            grouped = by_day(events.plan_week_events(FAMILY, DEV, today))
            window_days = week_days(today, 0) + week_days(today, 1)
            counts = [len(unique_events(grouped[day])) for day in window_days]
            self.assertIn(0, counts)
            self.assertIn(1, counts)
            self.assertIn(4, counts)
            this_week = counts[:7]
            self.assertGreaterEqual(sum(1 for c in this_week if 1 <= c <= 3), 5, (today, this_week))

    def test_every_key_is_valid_for_marker_and_unique_per_calendar(self) -> None:
        for today in DATES:
            plan = events.plan_week_events(FAMILY, DEV, today)
            seen = set()
            for item in plan:
                self.assertRegex(item.key, KEY_SHAPE)
                self.assertEqual(item.description, calendar_tags.marker(DEV, item.key))
                self.assertTrue(item.summary.startswith(DEV.tag))
                self.assertNotIn((item.entity_id, item.key), seen)
                seen.add((item.entity_id, item.key))

    def test_all_events_start_inside_the_window_and_all_day_ends_a_day_later(self) -> None:
        start, end = events.window(TODAY)
        for item in events.plan_week_events(FAMILY, DEV, TODAY):
            self.assertTrue(start <= item.start < end, item)
            self.assertGreater(item.end, item.start)
            if item.all_day:
                self.assertEqual(item.end - item.start, datetime.timedelta(days=1))

    def test_titles_come_from_the_s5_list(self) -> None:
        allowed = {"School drop-off", "Dentist", "Football practice", "Piano lesson", "Family movie night", "Grandma visits"}
        for item in events.plan_week_events(FAMILY, DEV, TODAY):
            self.assertIn(item.summary[len(DEV.tag):], allowed)


class PlanStabilityTests(unittest.TestCase):
    def test_desired_keys_are_identical_on_every_day_of_a_week(self) -> None:
        for week_start in (datetime.date(2026, 11, 2), datetime.date(2026, 11, 9)):
            plans = [events.plan_week_events(FAMILY, DEV, week_start + datetime.timedelta(days=n)) for n in range(7)]
            for plan in plans[1:]:
                self.assertEqual(plan, plans[0])

    def test_a_monday_rollover_only_adds_events_for_days_in_both_windows(self) -> None:
        for today in DATES[:-1]:
            old = by_day(events.plan_week_events(FAMILY, DEV, today))
            new = by_day(events.plan_week_events(FAMILY, DEV, today + datetime.timedelta(days=1)))
            common = set(week_days(today, 0) + week_days(today, 1)) & set(
                week_days(today + datetime.timedelta(days=1), 0) + week_days(today + datetime.timedelta(days=1), 1)
            )
            for day in common:
                old_keys = {(i.entity_id, i.key) for i in old[day]}
                new_keys = {(i.entity_id, i.key) for i in new[day]}
                self.assertTrue(old_keys <= new_keys, (today, day))

    def test_a_rollover_keeps_the_events_themselves_identical_not_just_the_keys(self) -> None:
        sunday = events.plan_week_events(FAMILY, DEV, datetime.date(2026, 11, 8))
        monday = events.plan_week_events(FAMILY, DEV, datetime.date(2026, 11, 9))
        next_week = set(week_days(datetime.date(2026, 11, 8), 1))
        before = [i for i in sunday if i.start.date() in next_week]
        after = {(i.entity_id, i.key): i for i in monday if i.start.date() in next_week}
        for item in before:
            self.assertEqual(after[(item.entity_id, item.key)], item)

    def test_next_week_keys_are_this_week_template_keys_for_that_weekday(self) -> None:
        this_week = {(t.weekday, t.slot, t.members, t.title, t.start, t.minutes) for t in events.THIS_WEEK}
        for t in events.NEXT_WEEK:
            self.assertIn((t.weekday, t.slot, t.members, t.title, t.start, t.minutes), this_week)

    def test_plan_is_sorted_and_building_twice_gives_equal_lists(self) -> None:
        first = events.plan_week_events(FAMILY, DEV, TODAY)
        second = events.plan_week_events(FAMILY, DEV, TODAY)
        self.assertEqual(first, second)
        self.assertEqual(first, sorted(first, key=lambda i: (i.start, i.entity_id, i.key)))


class PlanEdgeTests(unittest.TestCase):
    def test_one_writable_calendar_plans_without_the_shared_and_partial_rules(self) -> None:
        plan = events.plan_week_events([FAMILY[0]], DEV, TODAY)
        self.assertGreater(len(plan), 0)
        self.assertEqual({i.entity_id for i in plan}, {"calendar.sam"})
        keys = [i.key for i in plan]
        self.assertEqual(len(keys), len(set(keys)))

    def test_zero_slots_plan_nothing(self) -> None:
        self.assertEqual(events.plan_week_events([], DEV, TODAY), [])

    def test_a_read_only_slot_gets_no_events(self) -> None:
        slots = [CalendarSlot("Sam", "calendar.sam"), CalendarSlot("Jordan", "calendar.jordan", writable=False)]
        plan = events.plan_week_events(slots, DEV, TODAY)
        self.assertGreater(len(plan), 0)
        self.assertNotIn("calendar.jordan", {i.entity_id for i in plan})

    def test_only_read_only_slots_plan_nothing(self) -> None:
        self.assertEqual(events.plan_week_events([CalendarSlot("Sam", "calendar.sam", writable=False)], DEV, TODAY), [])

    def test_two_writable_calendars_still_share_the_movie_night(self) -> None:
        plan = events.plan_week_events(FAMILY[:2], DEV, TODAY)
        shared = [i for i in plan if i.key.endswith("-shared")]
        self.assertEqual({i.entity_id for i in shared if i.start.date() == datetime.date(2026, 11, 4)}, {"calendar.sam", "calendar.jordan"})

    def test_person_names_become_safe_key_slugs(self) -> None:
        slots = [CalendarSlot("Zoë O'Neil", "calendar.zoe"), CalendarSlot("!!!", "calendar.x")]
        for item in events.plan_week_events(slots, DEV, TODAY):
            self.assertRegex(item.key, KEY_SHAPE)


class CrossEnvironmentTests(unittest.TestCase):
    def test_no_dev_event_matches_the_preview_matcher_and_the_reverse(self) -> None:
        start, end = events.delete_window(TODAY)
        for env, other in ((DEV, PREVIEW), (PREVIEW, DEV)):
            plan = events.plan_week_events(FAMILY, env, TODAY)
            self.assertGreater(len(plan), 0)
            for item in plan:
                raw = to_raw(item)
                self.assertTrue(calendar_tags.matches(raw, env, item.entity_id, ALLOWED, start, end))
                self.assertFalse(calendar_tags.matches(raw, other, item.entity_id, ALLOWED, start, end))

    def test_dev_and_preview_keys_may_collide_but_never_the_markers(self) -> None:
        dev = {i.description for i in events.plan_week_events(FAMILY, DEV, TODAY)}
        preview = {i.description for i in events.plan_week_events(FAMILY, PREVIEW, TODAY)}
        self.assertEqual(dev & preview, set())


class DiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = events.plan_week_events(FAMILY, DEV, TODAY)

    def run_diff(self, existing, today=TODAY, allowed=ALLOWED):
        return events.diff(self.plan, existing, DEV, allowed, today)

    def test_nothing_existing_creates_everything(self) -> None:
        result = self.run_diff({slot.entity_id: [] for slot in FAMILY})
        self.assertEqual(result.create, self.plan)
        self.assertEqual((result.delete, result.keep), ([], []))

    def test_unchanged_existing_events_are_kept_and_nothing_else_happens(self) -> None:
        result = self.run_diff(existing_of(self.plan))
        self.assertEqual((len(result.create), len(result.delete), len(result.keep)), (0, 0, len(self.plan)))

    def test_a_desired_event_moved_by_thirty_minutes_is_deleted_and_created(self) -> None:
        existing = existing_of(self.plan)
        target = next(i for i in self.plan if not i.all_day)
        moved = target.start + datetime.timedelta(minutes=30)
        raw = next(r for r in existing[target.entity_id] if r["uid"] == "uid-%s-%s" % (target.entity_id, target.key))
        raw["start"] = {"dateTime": moved.isoformat() + "+00:00"}
        result = self.run_diff(existing)
        self.assertEqual([e.uid for e in result.delete], [raw["uid"]])
        self.assertEqual(result.create, [target])
        self.assertEqual(len(result.keep), len(self.plan) - 1)

    def test_a_renamed_event_is_deleted_and_created(self) -> None:
        existing = existing_of(self.plan)
        target = self.plan[0]
        existing[target.entity_id][0]["summary"] = DEV.tag + "Something else"
        result = self.run_diff(existing)
        self.assertEqual(len(result.delete), 1)
        self.assertEqual(result.create, [target])

    def test_an_all_day_event_that_became_timed_is_replaced(self) -> None:
        existing = existing_of(self.plan)
        target = next(i for i in self.plan if i.all_day)
        raw = next(r for r in existing[target.entity_id] if r["uid"] == "uid-%s-%s" % (target.entity_id, target.key))
        raw["start"] = {"dateTime": target.start.isoformat() + "+00:00"}
        result = self.run_diff(existing)
        self.assertEqual(result.create, [target])
        self.assertEqual(len(result.delete), 1)

    def test_duplicate_keys_are_deleted_after_the_first(self) -> None:
        existing = existing_of(self.plan)
        target = self.plan[0]
        existing[target.entity_id].append(to_raw(target, uid="zzz-duplicate"))
        result = self.run_diff(existing)
        self.assertEqual([e.uid for e in result.delete], ["zzz-duplicate"])
        self.assertEqual((len(result.create), len(result.keep)), (0, len(self.plan)))

    def test_a_stale_key_inside_the_delete_window_is_deleted(self) -> None:
        existing = existing_of(self.plan)
        last_week = events.plan_week_events(FAMILY, DEV, TODAY - datetime.timedelta(days=7))
        stale = next(i for i in last_week if i.start.date() < events.monday_of(TODAY))
        existing[stale.entity_id].append(to_raw(stale))
        result = self.run_diff(existing)
        self.assertEqual([e.key for e in result.delete], [stale.key])
        self.assertEqual(len(result.create), 0)

    def test_a_stale_tagged_event_older_than_the_delete_window_is_never_listed(self) -> None:
        existing = existing_of(self.plan)
        old = to_raw(self.plan[0], uid="ancient", start={"dateTime": "2026-09-01T10:00:00+00:00"})
        existing["calendar.sam"].append(old)
        result = self.run_diff(existing)
        everything = result.create and [] or result.delete + result.keep
        self.assertNotIn("ancient", [e.uid for e in everything])

    def test_events_that_fail_the_matcher_are_in_no_list(self) -> None:
        existing = existing_of(self.plan)
        target = self.plan[0]
        bad = {
            "untagged": to_raw(target, uid="untagged", summary="Dentist"),
            "other-env": to_raw(target, uid="other-env", summary="[PREVIEW] Dentist", description="family-hub-seed:preview:abc"),
            "no-marker": to_raw(target, uid="no-marker", description=None),
            "tag-in-middle": to_raw(target, uid="tag-in-middle", summary="Meeting [DEV] notes"),
            "marker-only": to_raw(target, uid="marker-only", summary="Piano", description="family-hub-seed:dev:piano"),
            "recurring": to_raw(target, uid="recurring", rrule="FREQ=DAILY", description="family-hub-seed:dev:rec"),
            "instance": to_raw(target, uid="instance", recurrence_id="20261104", description="family-hub-seed:dev:inst"),
            "trailing": to_raw(target, uid="trailing", description="family-hub-seed:dev:abc more"),
        }
        existing["calendar.sam"].extend(bad.values())
        result = self.run_diff(existing)
        listed = {e.uid for e in result.delete + result.keep}
        self.assertEqual(listed & set(bad), set())
        self.assertEqual((len(result.create), len(result.delete), len(result.keep)), (0, 0, len(self.plan)))

    def test_events_on_a_calendar_that_is_not_allowed_are_never_touched(self) -> None:
        existing = existing_of(self.plan)
        extra = to_raw(self.plan[0], uid="elsewhere", description="family-hub-seed:dev:stale-key")
        existing["calendar.family"] = [extra]
        result = self.run_diff(existing)
        self.assertNotIn("elsewhere", [e.uid for e in result.delete + result.keep])

    def test_nothing_is_created_on_a_calendar_that_is_not_allowed(self) -> None:
        result = events.diff(self.plan, {}, DEV, frozenset({"calendar.sam"}), TODAY)
        self.assertEqual({e.entity_id for e in result.create}, {"calendar.sam"})

    def test_monday_rollover_deletes_only_last_week_and_creates_only_missing_events(self) -> None:
        sunday, monday = datetime.date(2026, 11, 8), datetime.date(2026, 11, 9)
        old_plan = events.plan_week_events(FAMILY, DEV, sunday)
        new_plan = events.plan_week_events(FAMILY, DEV, monday)
        result = events.diff(new_plan, existing_of(old_plan), DEV, ALLOWED, monday)
        old_this_week = set(week_days(sunday, 0))
        self.assertTrue(all(day_of(e.start) in old_this_week for e in result.delete))
        self.assertEqual(len(result.delete), len([i for i in old_plan if i.start.date() in old_this_week]))
        old_keys = {(i.entity_id, i.key) for i in old_plan}
        self.assertEqual(
            {(e.entity_id, e.key) for e in result.create},
            {(i.entity_id, i.key) for i in new_plan} - old_keys,
        )
        # the week that was "next" gains the events next week's template left out; nothing there changes
        self.assertEqual({e.key.split("-")[0] for e in result.create}, {"2026w46", "2026w47"})
        kept_uids = {"uid-%s-%s" % (i.entity_id, i.key) for i in old_plan if i.start.date() not in old_this_week}
        self.assertEqual({e.uid for e in result.keep}, kept_uids)

    def test_second_diff_after_applying_the_first_is_empty(self) -> None:
        first = self.run_diff({slot.entity_id: [] for slot in FAMILY})
        applied = existing_of(first.create)
        again = self.run_diff(applied)
        self.assertEqual((again.create, again.delete), ([], []))

    def test_clean_style_diff_with_empty_desired_deletes_every_matching_event_only(self) -> None:
        existing = existing_of(self.plan)
        existing["calendar.sam"].append(to_raw(self.plan[0], uid="untagged", summary="Dentist"))
        result = events.diff([], existing, DEV, ALLOWED, TODAY)
        self.assertEqual(len(result.delete), len(self.plan))
        self.assertNotIn("untagged", [e.uid for e in result.delete])
        self.assertEqual((result.create, result.keep), ([], []))

    def test_diff_output_is_sorted(self) -> None:
        result = self.run_diff({slot.entity_id: [] for slot in FAMILY})
        self.assertEqual(result.create, sorted(result.create, key=DesiredEvent.sort_key))


class CommandLineTests(unittest.TestCase):
    def test_parse_calendar_reads_entity_person_and_read_only_flag(self) -> None:
        self.assertEqual(events.parse_calendar("calendar.sam=Sam"), CalendarSlot("Sam", "calendar.sam", True))
        self.assertEqual(events.parse_calendar("calendar.jo=Jordan:ro"), CalendarSlot("Jordan", "calendar.jo", False))

    def test_parse_calendar_refuses_bad_input(self) -> None:
        for bad in ("sam", "calendar.sam", "calendar.sam=", "light.kitchen=Sam", "calendar.Sam=Sam", "calendar.a b=Sam"):
            with self.assertRaises(argparse.ArgumentTypeError, msg=bad):
                events.parse_calendar(bad)

    def test_main_refuses_a_non_loopback_url_with_exit_2_before_connecting(self) -> None:
        code = events.main(["--target", "dev", "--base-url", "https://example.com", "plan", "--calendar", "calendar.sam=Sam"])
        self.assertEqual(code, 2)

    def test_main_refuses_the_same_calendar_twice(self) -> None:
        code = events.main(["--target", "dev", "plan", "--calendar", "calendar.sam=Sam", "--calendar", "calendar.sam=Sam2"])
        self.assertEqual(code, 2)

    def test_plan_command_prints_events_and_exits_0_without_connecting(self) -> None:
        import contextlib
        import io

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = events.main(["--target", "dev", "plan", "--calendar", "calendar.sam=Sam", "--today", "2026-11-04"])
        self.assertEqual(code, 0)
        self.assertIn("[DEV] Family movie night", out.getvalue())

    def test_plan_with_only_read_only_calendars_prints_nothing_and_exits_0(self) -> None:
        import contextlib
        import io

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = events.main(["--target", "dev", "plan", "--calendar", "calendar.sam=Sam:ro", "--today", "2026-11-04"])
        self.assertEqual((code, out.getvalue()), (0, ""))


if __name__ == "__main__":
    unittest.main()
