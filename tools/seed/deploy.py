"""Deploy-side checks and the hand-off note (PREV-05, PREV-07, D-19, D-20, ACCESS-05).

``verify_served`` proves that a deployed Preview really serves the card that deploy-preview
stamped: the build line in the served calendar card carries the stamp, no placeholder is left,
and every card's lovelace resource points at the hash of the file on disk with exactly one
resource per path. ``handoff_note`` builds the plain note the developer passes on to her (UI-SPEC S6).
"""
from __future__ import annotations

import re
import textwrap
from typing import Any, Callable, Optional

from . import resources as resources_mod
from . import verify as verify_mod
from .client import SeedError

# The stamp separator: a middle dot (U+00B7) with one space either side (UI-SPEC S3).
MIDDOT = "·"
STAMP_SEPARATOR = " %s " % MIDDOT

CARD_URL = "/family_hub_card/family-week-calendar-card.js"
CARD_FILE = "family-week-calendar-card.js"

NOTE_WIDTH = 72
NOTE_INDENT = 17

NO_WHAT = "(no note was given - tell her what changed yourself)"
NO_SCREEN = "(no screen was given - tell her where to tap yourself)"
READY_LINE = "Preview is updated and ready for you to try."

_BUILD_LINE = re.compile(r"^const __FH_BUILD\s*=.*$", re.MULTILINE)
_LEFTOVER_TOKEN = "__FH_BUILD_VERSION__"


def parse_stamp(stamp: str) -> tuple[str, str, str]:
    """Split ``<env> · <version>+<hash> · <time>`` into its three parts (all must be non-empty)."""
    parts = stamp.split(STAMP_SEPARATOR)
    if len(parts) != 3 or not all(part.strip() for part in parts) or any(p != p.strip() for p in parts):
        raise SeedError(
            "stamp",
            "the stamp %r is not '<env> %s <version>+<hash> %s <time>' (separator is U+00B7 with spaces)"
            % (stamp, MIDDOT, MIDDOT),
        )
    return parts[0], parts[1], parts[2]


def check_served_card(body: Any, stamp: str) -> list[str]:
    """Problems with the served calendar card body: stamp missing or a placeholder still in it."""
    env, version, deployed = parse_stamp(stamp)
    if not isinstance(body, str):
        return ["the served card is not JavaScript text"]
    problems: list[str] = []
    line = _BUILD_LINE.search(body)
    if line is None:
        problems.append("the served card has no 'const __FH_BUILD' line")
    else:
        for field, value in (("env", env), ("version", version), ("deployed", deployed)):
            if '%s: "%s"' % (field, value) not in line.group(0):
                problems.append("the served build line does not say %s: %r (it says: %s)" % (field, value, line.group(0)))
    if _LEFTOVER_TOKEN in body:
        problems.append("the served card still contains %s (the stamp was not substituted)" % _LEFTOVER_TOKEN)
    return problems


async def verify_served(
    client: Any,
    token: str,
    integration_dir: str,
    expect: str,
    say: Callable[[str], None] = print,
) -> None:
    """Raise SeedError listing every mismatch, or print ``served: <expect> OK``."""
    problems: list[str] = []

    status, body = await client.rest("GET", CARD_URL, token=token)
    if status != 200:
        problems.append("GET %s answered HTTP %s" % (CARD_URL, status))
    else:
        problems.extend(check_served_card(body, expect))

    files = resources_mod.served_js_files(integration_dir)
    if not files:
        raise SeedError("resources", "no card/ or panel/ files found in %s" % integration_dir)
    urls = resources_mod.served_urls(integration_dir)
    ws = await client.ws(token)
    resources = (await ws.call("lovelace/resources"))["result"]
    problems.extend(verify_mod.check_resources(resources, files, urls))

    if problems:
        raise SeedError(
            "not_served",
            "Preview is not serving what was deployed (%d problem%s): %s"
            % (len(problems), "" if len(problems) == 1 else "s", "; ".join(problems)),
        )
    say("served: %s OK" % expect)


def _one_line(text: Optional[str]) -> str:
    """Collapse any whitespace (including newlines) so one sentence stays one sentence."""
    return " ".join((text or "").split())


def _wrapped(first_prefix: str, text: str) -> list[str]:
    """Wrap ``text`` after ``first_prefix`` at NOTE_WIDTH code points; later lines are indented."""
    return textwrap.wrap(
        text,
        width=NOTE_WIDTH,
        initial_indent=first_prefix,
        subsequent_indent=" " * NOTE_INDENT,
        break_long_words=True,
        break_on_hyphens=False,
    )


def where_to_look(view: Optional[str], tap: Optional[str]) -> list[str]:
    """The 'Where to look' lines for whatever screen information was given."""
    view, tap = _one_line(view), _one_line(tap)
    prefix = "Where to look: "
    if not view and not tap:
        return _wrapped(prefix, "Open Family Hub PREVIEW.") + _wrapped(" " * NOTE_INDENT, NO_SCREEN)
    if view and tap:
        text = "Open Family Hub PREVIEW, tap %s, then %s." % (view, tap)
    elif view:
        text = "Open Family Hub PREVIEW, tap %s." % view
    else:
        text = "Open Family Hub PREVIEW, then %s." % tap
    return _wrapped(prefix, text)


def handoff_note(
    stamp: str,
    what: Optional[str] = None,
    view: Optional[str] = None,
    tap: Optional[str] = None,
) -> list[str]:
    """The UI-SPEC S6 hand-off note as lines of at most 72 code points."""
    parse_stamp(stamp)
    lines = [READY_LINE, ""]
    lines += _wrapped("What changed:  ", _one_line(what) or NO_WHAT)
    lines += where_to_look(view, tap)
    lines += _wrapped(
        "Check it is new: ", "the small line at the bottom of the Calendar should say"
    )
    lines += _wrapped(" " * NOTE_INDENT, '"%s".' % stamp)
    return lines
