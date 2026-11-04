"""Command line for the seed tool: python -m tools.seed --target {dev,preview} COMMAND.

Exit codes: 0 ok, 1 a seed step failed, 2 a guard refused (or bad usage), 3 identity mismatch.
The guards run before any connection is opened: the base URL must be https on a loopback
address, and TLS is verified against the local CA.
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import logging
import os
import sys
import time
from typing import Awaitable, Callable, Optional

from . import bootstrap as bootstrap_mod
from . import dashboard as dashboard_mod
from . import content as content_mod
from . import deploy as deploy_mod
from . import entries as entries_mod
from . import events
from . import family_file as family_file_mod
from . import family_hub as family_hub_mod
from . import google as google_mod
from . import resources as resources_mod
from . import users as users_mod
from . import verify as verify_mod
from .client import HAClient, HAWebSocket, SeedError
from .creds import CredentialStore
from .envs import ENVIRONMENTS, Env, GuardRefused, base_url, get_env
from .family_file import FamilyFileError

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class Context:
    """Everything a command needs; built once after the guards passed."""

    env: Env
    base_url: str
    ca: str
    secrets_dir: str
    timeout: float
    args: argparse.Namespace

    def client(self) -> HAClient:
        return HAClient(self.base_url, self.ca)

    def creds(self) -> CredentialStore:
        return CredentialStore(self.secrets_dir, self.env.key)


@dataclasses.dataclass
class Command:
    """One subcommand. Later plans register more entries in COMMANDS."""

    help: str
    run: Callable[[Context], Awaitable[int]]
    configure: Optional[Callable[[argparse.ArgumentParser], None]] = None


def say(line: str) -> None:
    print(line, flush=True)


async def _cmd_wait(ctx: Context) -> int:
    async with ctx.client() as client:
        await bootstrap_mod.wait_http(client, ctx.timeout, say)
    return 0


async def _cmd_bootstrap(ctx: Context) -> int:
    async with ctx.client() as client:
        await bootstrap_mod.bootstrap(client, ctx.env, ctx.creds(), ctx.timeout, say)
    return 0


# Where each target's served cards live: Dev mounts the working copy, Preview runs an exported copy.
DEFAULT_INTEGRATION_DIR = {
    "dev": "custom_components/family_hub",
    "preview": "dev/.ha-preview/custom_components/family_hub",
}


def _configure_resources_sync(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--integration-dir", default=None, help="directory holding card/ and panel/")
    parser.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")


async def _cmd_resources_sync(ctx: Context) -> int:
    integration_dir = ctx.args.integration_dir or DEFAULT_INTEGRATION_DIR[ctx.env.key]
    async with ctx.client() as client:
        token, _ws = await bootstrap_mod.open_admin(client, ctx.env, ctx.creds())
        await resources_mod.sync(client, token, integration_dir, apply=not ctx.args.dry_run, say=say)
    return 0


def _configure_family(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--family", default=None, help="family file (default: family.local.yaml, else the example)")
    parser.add_argument("--integration-dir", default=None, help="directory holding card/ and panel/")


async def _verify(ctx: Context, client: HAClient, token: str, ws, family, creds) -> int:
    """Run verify against the instance; 1 when anything failed."""
    integration_dir = ctx.args.integration_dir or DEFAULT_INTEGRATION_DIR[ctx.env.key]
    failures = await verify_mod.run_verify(client, token, ws, ctx.env, family, creds, integration_dir, say)
    return 1 if failures else 0


async def _cmd_verify(ctx: Context) -> int:
    family = family_file_mod.load(ctx.args.family, say)
    async with ctx.client() as client:
        token, ws = await bootstrap_mod.open_admin(client, ctx.env, ctx.creds())
        return await _verify(ctx, client, token, ws, family, ctx.creds())


async def _google_setup(
    ctx: Context, client: HAClient, token: str, ws: HAWebSocket, family, reload: bool
) -> tuple[dict[str, str], list[events.CalendarSlot]]:
    """Make the Google connection ready: credential, entry loaded, only the chosen calendars enabled.

    Returns ``(first name -> Google calendar entity, Google event slots)``; both are empty when the
    family file has no google block. An entry that cannot load stops the run here with the
    one-time sign-in instruction. ``reload`` is False for a refresh, which only checks the entry.
    """
    if not family.google:
        return {}, []
    entry = await google_mod.link(client, token, ws, family.google, ctx.env, say, reload=reload)
    keys = await google_mod.apply_selection(ws, entry, family.google, say)
    return google_mod.member_calendars(family, keys), google_mod.google_slots(family, keys)


async def _cmd_seed(ctx: Context) -> int:
    """Bootstrap, then turn the onboarded instance into what she sees: accounts, lists, Family Hub,
    her dashboard and her sidebar. Every step is a top-up, so running it again changes nothing."""
    family = family_file_mod.load(ctx.args.family, say)
    async with ctx.client() as client:
        await bootstrap_mod.bootstrap(client, ctx.env, ctx.creds(), ctx.timeout, say)
        token, ws = await bootstrap_mod.open_admin(client, ctx.env, ctx.creds())
        creds = ctx.creds()
        await family_hub_mod.remove_outbound_entries(client, token, say)
        # The accounts come first, so on the very first run (no Google sign-in yet) the developer's own
        # account already exists to sign in with. Google comes before Family Hub: a member's calendar
        # may be a Google entity.
        user_ids = await users_mod.ensure_users(ws, creds, family, say)
        await entries_mod.ensure_todo_lists(client, token, ws, say)
        google_members, google_slots = await _google_setup(ctx, client, token, ws, family, reload=True)
        calendars = await entries_mod.ensure_local_calendars(client, token, ws, family, say)
        calendars.update(google_members)
        await entries_mod.ensure_family_hub_entry(client, token, ws, family, user_ids, calendars, say)
        await dashboard_mod.ensure_dashboard(ws, ctx.env, family, calendars, say)
        today, zone = await family_hub_mod.instance_today(ws)
        week = content_mod.build_content(family, ctx.env, today)
        await family_hub_mod.apply_content(ws, family, user_ids, week, creds, ctx.env, zone, say)
        slots = entries_mod.calendar_slots(family, calendars, google_slots)
        await events.sync(client, token, slots, ctx.env, today, apply=True, say=say)
        await family_hub_mod.apply_safe_notifications(ws, say)
        for member in family.members:
            if not member.admin:
                hidden = await dashboard_mod.set_member_sidebar(client, creds, member)
                say("sidebar: %s sees Family Hub only (%d panels hidden)" % (member.first_name, len(hidden)))
        return await _verify(ctx, client, token, ws, family, creds)


def _configure_verify_served(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expect", required=True, help="the build stamp deploy-preview wrote, e.g. 'Preview · 2.0.0+a1b2c3d · 4 Nov 14:05'")
    parser.add_argument("--integration-dir", default=None, help="directory holding card/ and panel/")


async def _cmd_verify_served(ctx: Context) -> int:
    """Prove the instance serves the stamped card and one up-to-date resource per card."""
    integration_dir = ctx.args.integration_dir or DEFAULT_INTEGRATION_DIR[ctx.env.key]
    async with ctx.client() as client:
        token, _ws = await bootstrap_mod.open_admin(client, ctx.env, ctx.creds())
        await deploy_mod.verify_served(client, token, integration_dir, ctx.args.expect, say)
    return 0


def _configure_note(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--stamp", required=True, help="the build stamp the note tells her to look for")
    parser.add_argument("--what", default=None, help="one plain sentence: what changed")
    parser.add_argument("--view", default=None, help="the tab to open, e.g. Chores")
    parser.add_argument("--tap", default=None, help="what to tap there, e.g. the + button")


async def _cmd_note(ctx: Context) -> int:
    """Print the hand-off note (no connection to Home Assistant is made)."""
    for line in deploy_mod.handoff_note(ctx.args.stamp, ctx.args.what, ctx.args.view, ctx.args.tap):
        say(line)
    return 0


# Errors that only mean "Home Assistant is still starting": retried for a while by refresh.
_STARTING_UP = ("auth", "connect", "ws_error")
_STARTUP_PATIENCE = 120.0


async def _open_running_admin(ctx: Context, client: HAClient) -> tuple[str, HAWebSocket]:
    """Log in as the tool's admin (identity guard first) and wait until Home Assistant is RUNNING.

    A refresh runs at logon, possibly right after Docker restarted Preview, so a login or
    connection that fails while HA is still starting is retried for a couple of minutes. A wrong
    name (identity) or an unusable CA is never retried.
    """
    deadline = time.monotonic() + min(ctx.timeout, _STARTUP_PATIENCE)
    while True:
        try:
            token, ws = await bootstrap_mod.open_admin(client, ctx.env, ctx.creds())
            await bootstrap_mod.wait_running(ws, ctx.timeout, say)
            return token, ws
        except SeedError as err:
            if err.code not in _STARTING_UP or time.monotonic() >= deadline:
                raise
            await asyncio.sleep(3)


def _stderr(line: str) -> None:
    print(line, file=sys.stderr, flush=True)


def _configure_family_only(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--family", default=None, help="family file (default: family.local.yaml, else the example)")


def _configure_google_save(parser: argparse.ArgumentParser) -> None:
    _configure_family_only(parser)
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--stdin", action="store_true", help="read the stopped instance's core.config_entries from stdin")
    where.add_argument("--config-dir", default=None, help="read DIR/.storage/core.config_entries")


async def _cmd_google_save(ctx: Context) -> int:
    """Keep the stopped instance's Google sign-in in the secrets directory (before a wipe)."""
    if ctx.args.stdin:
        text = sys.stdin.read()  # always consumed, so the producer never meets a closed pipe
    else:
        path = os.path.join(ctx.args.config_dir, ".storage", "core.config_entries")
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except FileNotFoundError:
            say("google: no entry to save")
            return 0
    if not family_file_mod.load(ctx.args.family, _stderr).google:
        return 0
    google_mod.save_entry(text, ctx.secrets_dir, ctx.env, say)
    return 0


def _configure_google_restore(parser: argparse.ArgumentParser) -> None:
    _configure_family_only(parser)
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--stdout", action="store_true", help="print the core.config_entries text to write")
    where.add_argument("--config-dir", default=None, help="write DIR/.storage/core.config_entries (a wiped directory)")


async def _cmd_google_restore(ctx: Context) -> int:
    """Hand back the saved Google sign-in as the only config entry, for a wiped directory."""
    target = None
    if ctx.args.config_dir:
        target = os.path.join(ctx.args.config_dir, ".storage", "core.config_entries")
        if os.path.exists(target):
            _stderr("refused: %s already exists; the Google entry is only restored into a wiped directory" % target)
            return 2
    if not family_file_mod.load(ctx.args.family, _stderr).google:
        return 0
    text = google_mod.restore_entry(ctx.secrets_dir, ctx.env)
    if text is None:
        _stderr("google: no saved entry for %s" % ctx.env.key)
        return 0
    if target is None:
        sys.stdout.write(text)
        sys.stdout.flush()
        return 0
    os.makedirs(os.path.dirname(target), exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    say("google: entry restored into %s" % target)
    return 0


async def _cmd_google_link(ctx: Context) -> int:
    """Create the application credential and reload the Google entry until it is loaded."""
    family = family_file_mod.load(ctx.args.family, say)
    if not family.google:
        say("google: not configured")
        return 0
    async with ctx.client() as client:
        token, ws = await bootstrap_mod.open_admin(client, ctx.env, ctx.creds())
        await google_mod.link(client, token, ws, family.google, ctx.env, say)
    return 0


def _configure_backup(parser: argparse.ArgumentParser) -> None:
    _configure_family_only(parser)
    parser.add_argument("--backups-dir", default="dev/.ha-backups", help="where the dated backup folders go")


async def _cmd_backup_calendars(ctx: Context) -> int:
    """Placeholder: replaced by the real backup in the next commit."""
    return 0


async def _cmd_refresh(ctx: Context) -> int:
    """Keep the week current without starting over: top up her content, sync the pretend events,
    put the safe notification settings back and verify. Everything here only adds or corrects;
    the Family Hub data she and the family created is left exactly as it is."""
    family = family_file_mod.load(ctx.args.family, say)
    async with ctx.client() as client:
        await bootstrap_mod.wait_http(client, ctx.timeout, say)
        token, ws = await _open_running_admin(ctx, client)
        creds = ctx.creds()
        await family_hub_mod.remove_outbound_entries(client, token, say)
        _google_members, google_slots = await _google_setup(ctx, client, token, ws, family, reload=False)
        user_ids = await users_mod.ensure_users(ws, creds, family, say)
        calendars = await entries_mod.ensure_local_calendars(client, token, ws, family, say)
        today, zone = await family_hub_mod.instance_today(ws)
        week = content_mod.build_content(family, ctx.env, today)
        await family_hub_mod.apply_content(ws, family, user_ids, week, creds, ctx.env, zone, say)
        slots = entries_mod.calendar_slots(family, calendars, google_slots)
        await events.sync(client, token, slots, ctx.env, today, apply=True, say=say)
        await family_hub_mod.apply_safe_notifications(ws, say)
        return await _verify(ctx, client, token, ws, family, creds)


COMMANDS: dict[str, Command] = {
    "wait": Command("wait until Home Assistant answers over verified TLS", _cmd_wait),
    "bootstrap": Command(
        "onboard, promote the http config and name the instance", _cmd_bootstrap
    ),
    "seed": Command(
        "bootstrap, then create her accounts, lists, Family Hub, dashboard and sidebar, then verify",
        _cmd_seed,
        _configure_family,
    ),
    "verify": Command(
        "fail if anything could reach a real phone or anything she relies on is missing",
        _cmd_verify,
        _configure_family,
    ),
    "refresh": Command(
        "top up her week, sync the pretend events, re-apply safe notifications and verify (never wipes)",
        _cmd_refresh,
        _configure_family,
    ),
    "verify-served": Command(
        "fail unless the instance serves the stamped calendar card and one fresh resource per card",
        _cmd_verify_served,
        _configure_verify_served,
    ),
    "note": Command(
        "print the plain hand-off note for her after a deploy",
        _cmd_note,
        _configure_note,
    ),
    "google-save": Command(
        "keep the stopped instance's Google sign-in in the secrets directory (before a wipe)",
        _cmd_google_save,
        _configure_google_save,
    ),
    "google-restore": Command(
        "hand back the saved Google sign-in as the only config entry (into a wiped directory)",
        _cmd_google_restore,
        _configure_google_restore,
    ),
    "google-link": Command(
        "create the Google application credential and reload the entry until it is loaded",
        _cmd_google_link,
        _configure_family_only,
    ),
    "backup-calendars": Command(
        "save every chosen Google calendar to a dated .ics file; stops hard if any backup fails",
        _cmd_backup_calendars,
        _configure_backup,
    ),
    "resources-sync": Command(
        "point each card's lovelace resource at the hash of the file being served",
        _cmd_resources_sync,
        _configure_resources_sync,
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.seed", description=__doc__.split("\n")[0])
    parser.add_argument("--target", required=True, choices=sorted(ENVIRONMENTS))
    parser.add_argument("--base-url", default=None, help="override; must be https on a loopback host")
    parser.add_argument("--ca", default="dev/.ha-certs/ca.crt", help="CA file used to verify TLS")
    parser.add_argument("--secrets-dir", default="dev/.ha-secrets")
    parser.add_argument("--timeout", type=float, default=600.0, help="seconds to wait for Home Assistant")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, command in COMMANDS.items():
        subparser = sub.add_parser(name, help=command.help)
        if command.configure is not None:
            command.configure(subparser)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        env = get_env(args.target)
        url = base_url(env, args.base_url)
    except GuardRefused as err:
        print("refused: %s" % err, file=sys.stderr)
        return err.exit_code
    ctx = Context(env, url, args.ca, args.secrets_dir, args.timeout, args)
    try:
        return asyncio.run(COMMANDS[args.command].run(ctx))
    except GuardRefused as err:
        print("refused: %s" % err, file=sys.stderr)
        return err.exit_code
    except FamilyFileError as err:
        print("family file: %s" % err, file=sys.stderr)
        return err.exit_code
    except SeedError as err:
        print("error [%s]: %s" % (err.code, err.message), file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    sys.exit(main())
