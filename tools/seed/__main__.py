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
from .client import HAClient, SeedError
from .creds import CredentialStore
from .envs import ENVIRONMENTS, Env, GuardRefused, base_url, get_env

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


COMMANDS: dict[str, Command] = {
    "wait": Command("wait until Home Assistant answers over verified TLS", _cmd_wait),
    "bootstrap": Command(
        "onboard, promote the http config and name the instance", _cmd_bootstrap
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
    except SeedError as err:
        print("error [%s]: %s" % (err.code, err.message), file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    sys.exit(main())
