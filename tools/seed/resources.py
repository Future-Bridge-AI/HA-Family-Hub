"""resources-sync: keep each card's lovelace resource URL on the hash of the file being served.

A browser reload does not reliably pick up an edited card file: the module URL has to change.
The integration puts ``?v=<sha256(file)[:10]>`` on every card URL, but only when it starts, so
after an edit in Dev this tool rewrites the resource URLs the same way (Python changes still
need a restart; card changes need only this and a normal refresh).

Rules that keep it safe to run again and again, even after an interrupted run:
- a resource is matched to a served file by the basename of its URL path (query stripped);
- only a changed hash causes an update, and a card file with no resource at all gets a create;
- a second resource for one path is an error, never a create (two resources make
  customElements.define throw).
"""
from __future__ import annotations

import glob
import hashlib
import os
import re
from typing import Any, Callable, Optional

from .client import SeedError

_JS_URL_CONSTANT = re.compile(r'^[A-Z][A-Z0-9_]*_JS_URL\s*=\s*"([^"]+)"', re.MULTILINE)


def served_js_files(integration_dir: str) -> dict[str, str]:
    """Map basename to path for every card/*.js and panel/*.js the integration serves."""
    files: dict[str, str] = {}
    for sub in ("card", "panel"):
        for path in sorted(glob.glob(os.path.join(integration_dir, sub, "*.js"))):
            files[os.path.basename(path)] = path
    return files


def served_urls(integration_dir: str) -> dict[str, str]:
    """Map basename to served URL path, read from the integration's own *_JS_URL constants."""
    try:
        with open(os.path.join(integration_dir, "const.py"), encoding="utf-8") as handle:
            text = handle.read()
    except OSError as err:
        raise SeedError("resources", "cannot read const.py in %s: %s" % (integration_dir, err)) from err
    return {url.rsplit("/", 1)[-1]: url for url in _JS_URL_CONSTANT.findall(text)}


def content_hash(path: str) -> str:
    """Same hash as the integration's _file_content_hash: sha256 of the bytes, first 10 hex."""
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()[:10]
    except OSError as err:
        raise SeedError("resources", "cannot read %s: %s" % (path, err)) from err


def _basename(url: str) -> str:
    return url.split("?", 1)[0].rsplit("/", 1)[-1]


def plan_updates(
    resources: list[dict], files: dict[str, str], urls: Optional[dict[str, str]] = None
) -> list[dict]:
    """Return the actions that bring ``resources`` in line with ``files``.

    Actions: ``update`` (changed hash), ``create`` (a served *-card.js with no resource, URL
    taken from ``urls``) and ``duplicate`` (two resources share one file; nothing is planned for
    that file). An unchanged resource and a resource that is not a served file produce nothing.
    """
    by_name: dict[str, list[dict]] = {}
    for resource in resources:
        name = _basename(resource.get("url") or "")
        if name in files:
            by_name.setdefault(name, []).append(resource)

    actions: list[dict] = []
    for name in sorted(files):
        rows = by_name.get(name, [])
        if len(rows) > 1:
            actions.append(
                {"action": "duplicate", "file": name, "resource_ids": [row["id"] for row in rows]}
            )
        elif len(rows) == 1:
            row = rows[0]
            wanted = "%s?v=%s" % (row["url"].split("?", 1)[0], content_hash(files[name]))
            if row["url"] != wanted:
                actions.append(
                    {"action": "update", "resource_id": row["id"], "url": wanted, "old_url": row["url"]}
                )
        elif name.endswith("-card.js") and urls and name in urls:
            actions.append({"action": "create", "url": "%s?v=%s" % (urls[name], content_hash(files[name]))})
    return actions


def _raise_on_duplicates(plan: list[dict]) -> None:
    duplicates = [action for action in plan if action["action"] == "duplicate"]
    if duplicates:
        detail = "; ".join(
            "%s has resources %s" % (item["file"], ", ".join(item["resource_ids"])) for item in duplicates
        )
        raise SeedError(
            "duplicate",
            "more than one lovelace resource for a served file (%s): delete the extra rows in "
            "Settings > Dashboards > Resources, nothing was changed" % detail,
        )


async def sync(
    client: Any,
    token: str,
    integration_dir: str,
    apply: bool = True,
    say: Callable[[str], None] = print,
) -> dict:
    """Rewrite changed resource URLs (and create missing card resources); return the counts."""
    files = served_js_files(integration_dir)
    if not files:
        raise SeedError("resources", "no card/ or panel/ files found in %s" % integration_dir)
    urls = served_urls(integration_dir)
    ws = await client.ws(token)

    resources = (await ws.call("lovelace/resources"))["result"]
    plan = plan_updates(resources, files, urls)
    _raise_on_duplicates(plan)

    updates = [action for action in plan if action["action"] == "update"]
    creates = [action for action in plan if action["action"] == "create"]
    matched = sum(1 for resource in resources if _basename(resource.get("url") or "") in files)
    counts = {"updated": len(updates), "created": len(creates), "unchanged": matched - len(updates)}

    if apply:
        for action in updates:
            await ws.call("lovelace/resources/update", resource_id=action["resource_id"], url=action["url"])
        for action in creates:
            await ws.call("lovelace/resources/create", res_type="module", url=action["url"])
        if updates or creates:
            # The integration registers its own resources at start-up; make sure the two
            # writers did not leave a second row behind for any path.
            after = (await ws.call("lovelace/resources"))["result"]
            _raise_on_duplicates(plan_updates(after, files, urls))

    suffix = "" if apply else " (dry run, nothing written)"
    say(
        "resources: %d updated, %d created, %d unchanged%s"
        % (counts["updated"], counts["created"], counts["unchanged"], suffix)
    )
    return counts
