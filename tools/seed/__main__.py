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
import sys
from typing import Awaitable, Callable, Optional

from . import bootstrap as bootstrap_mod
from . import dashboard as dashboard_mod
from . import entries as entries_mod
from . import family_file as family_file_mod
from . import resources as resources_mod
from . import users as users_mod
from .client import HAClient, SeedError
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


def _configure_seed(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--family", default=None, help="family file (default: family.local.yaml, else the example)")


async def _cmd_seed(ctx: Context) -> int:
    """Bootstrap, then turn the onboarded instance into what she sees: accounts, lists, Family Hub,
    her dashboard and her sidebar. Every step is a top-up, so running it again changes nothing."""
    family = family_file_mod.load(ctx.args.family, say)
    async with ctx.client() as client:
        await bootstrap_mod.bootstrap(client, ctx.env, ctx.creds(), ctx.timeout, say)
        token, ws = await bootstrap_mod.open_admin(client, ctx.env, ctx.creds())
        creds = ctx.creds()
        user_ids = await users_mod.ensure_users(ws, creds, family, say)
        await entries_mod.ensure_todo_lists(client, token, ws, say)
        calendars = await entries_mod.ensure_local_calendars(client, token, ws, family, say)
        await entries_mod.ensure_family_hub_entry(client, token, ws, family, user_ids, calendars, say)
        await dashboard_mod.ensure_dashboard(ws, ctx.env, family, calendars, say)
        for member in family.members:
            if not member.admin:
                hidden = await dashboard_mod.set_member_sidebar(client, creds, member)
                say("sidebar: %s sees Family Hub only (%d panels hidden)" % (member.first_name, len(hidden)))
    return 0


COMMANDS: dict[str, Command] = {
    "wait": Command("wait until Home Assistant answers over verified TLS", _cmd_wait),
    "bootstrap": Command(
        "onboard, promote the http config and name the instance", _cmd_bootstrap
    ),
    "seed": Command(
        "bootstrap, then create her accounts, lists, Family Hub, dashboard and sidebar",
        _cmd_seed,
        _configure_seed,
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
