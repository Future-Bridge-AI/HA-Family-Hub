"""Home Assistant client for the seed tool: REST, login flow, WebSocket and config flows.

TLS is always verified against the local CA file (scripts/make-certs). A missing CA file is an
error, never a fallback to an unverified connection, so a certificate that does not chain to the
local CA (for example the family's real Home) fails before credentials are sent.
"""
from __future__ import annotations

import asyncio
import json as jsonlib
import logging
import os
import ssl
from typing import Any, Callable, Optional, Union

import aiohttp

_LOGGER = logging.getLogger(__name__)

Answer = Union[dict, list, Callable[[dict], dict]]


class SeedError(Exception):
    """A seed step failed. ``code`` is machine readable; "identity" maps to exit code 3."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    @property
    def exit_code(self) -> int:
        return 3 if self.code == "identity" else 1


class HAWebSocket:
    """An authenticated WebSocket connection; ``call`` returns the full result message."""

    def __init__(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        self._ws = ws
        self._next_id = 1

    async def call(self, type: str, **fields: Any) -> dict:
        """Send ``{id, type, **fields}`` and wait for its result message.

        Returns the whole message, so the payload is ``reply["result"]``. Raises SeedError
        (code = the HA error code) when HA answers ``success: false``.
        """
        msg_id = self._next_id
        self._next_id += 1
        await self._ws.send_json({"id": msg_id, "type": type, **fields})
        while True:
            msg = await self._ws.receive_json()
            if msg.get("id") != msg_id or msg.get("type") != "result":
                continue  # events and other ids
            if not msg.get("success"):
                error = msg.get("error") or {}
                raise SeedError(
                    str(error.get("code", "ws_error")),
                    "%s failed: %s" % (type, error.get("message", msg)),
                )
            return msg

    async def close(self) -> None:
        await self._ws.close()


class HAClient:
    """One aiohttp session against one Home Assistant base URL, verified by a local CA."""

    def __init__(self, base_url: str, ca_file: str, request_timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.ca_file = ca_file
        self.client_id = self.base_url + "/"
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._ssl: Optional[ssl.SSLContext] = None
        self._sockets: list[HAWebSocket] = []

    async def __aenter__(self) -> "HAClient":
        if not os.path.isfile(self.ca_file):
            raise SeedError(
                "ca",
                "CA file %s not found: run scripts/make-certs first (TLS is never skipped)"
                % self.ca_file,
            )
        try:
            self._ssl = ssl.create_default_context(cafile=self.ca_file)
        except (ssl.SSLError, OSError) as err:
            raise SeedError("ca", "CA file %s is not usable: %s" % (self.ca_file, err)) from err
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self._ssl), timeout=self._timeout
        )
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        for sock in self._sockets:
            try:
                await sock.close()
            except Exception as err:  # best effort on shutdown
                _LOGGER.debug("closing websocket failed: %s", err)
        if self._session is not None:
            await self._session.close()

    def _map_connection_error(self, err: Exception) -> SeedError:
        if isinstance(err, (aiohttp.ClientSSLError, ssl.SSLError)):
            return SeedError(
                "tls",
                "TLS verification failed for %s against %s: %s"
                % (self.base_url, self.ca_file, err),
            )
        if isinstance(err, asyncio.TimeoutError):
            return SeedError("connect", "timed out talking to %s" % self.base_url)
        return SeedError("connect", "cannot reach %s: %s" % (self.base_url, err))

    async def rest(
        self,
        method: str,
        path: str,
        json: Any = None,
        data: Any = None,
        token: Optional[str] = None,
    ) -> tuple[int, Any]:
        """Call ``path`` and return ``(status, body)``; body is parsed JSON when possible."""
        assert self._session is not None, "use HAClient as an async context manager"
        headers = {"Authorization": "Bearer " + token} if token else None
        try:
            async with self._session.request(
                method, self.base_url + path, json=json, data=data, headers=headers
            ) as resp:
                text = await resp.text()
                try:
                    body: Any = jsonlib.loads(text) if text else None
                except ValueError:
                    body = text
                return resp.status, body
        except (aiohttp.ClientError, ssl.SSLError, asyncio.TimeoutError) as err:
            raise self._map_connection_error(err) from err

    async def login(self, username: str, password: str) -> str:
        """Log in through the login flow and return a short-lived access token."""
        redirect = self.client_id + "?auth_callback=1"
        status, body = await self.rest(
            "POST",
            "/auth/login_flow",
            json={
                "client_id": self.client_id,
                "handler": ["homeassistant", None],
                "redirect_uri": redirect,
            },
        )
        if status != 200 or not isinstance(body, dict) or "flow_id" not in body:
            raise SeedError("auth", "login flow could not start (HTTP %s)" % status)
        status, body = await self.rest(
            "POST",
            "/auth/login_flow/%s" % body["flow_id"],
            json={"client_id": self.client_id, "username": username, "password": password},
        )
        if status != 200 or not isinstance(body, dict) or body.get("type") != "create_entry":
            errors = body.get("errors") if isinstance(body, dict) else body
            raise SeedError("auth", "login as %s failed: %s" % (username, errors))
        return await self.exchange_code(body["result"])

    async def exchange_code(self, code: str) -> str:
        """Exchange an authorization code for an access token."""
        status, body = await self.rest(
            "POST",
            "/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
            },
        )
        if status != 200 or not isinstance(body, dict) or "access_token" not in body:
            raise SeedError("auth", "token exchange failed (HTTP %s)" % status)
        return body["access_token"]

    async def ws(self, token: str) -> HAWebSocket:
        """Open and authenticate a WebSocket; it is closed when the client exits."""
        assert self._session is not None, "use HAClient as an async context manager"
        url = "wss" + self.base_url[len("https"):] + "/api/websocket"
        try:
            raw = await self._session.ws_connect(url)
            hello = await raw.receive_json()
            if hello.get("type") != "auth_required":
                raise SeedError("ws_error", "unexpected websocket greeting: %s" % hello)
            await raw.send_json({"type": "auth", "access_token": token})
            reply = await raw.receive_json()
        except (aiohttp.ClientError, ssl.SSLError, asyncio.TimeoutError) as err:
            raise self._map_connection_error(err) from err
        if reply.get("type") != "auth_ok":
            await raw.close()
            raise SeedError("auth", "websocket authentication refused: %s" % reply)
        sock = HAWebSocket(raw)
        self._sockets.append(sock)
        return sock

    async def drive_config_flow(self, token: str, handler: str, answers: dict[str, Answer]) -> dict:
        """Run a config flow to ``create_entry``, answering each form from ``answers[step_id]``.

        An answer is a dict, a list of dicts consumed in order (a step that repeats, such as
        Family Hub's member_profile loop), or a callable taking the step JSON (so it can read
        ``description_placeholders``) and returning a dict. A flow that fails half way is aborted
        on the server, so the next run is not blocked by an "already in progress" flow.
        """
        queues: dict[str, Any] = {
            key: (list(value) if isinstance(value, list) else value)
            for key, value in answers.items()
        }
        status, step = await self.rest(
            "POST",
            "/api/config/config_entries/flow",
            json={"handler": handler, "show_advanced_options": False},
            token=token,
        )
        flow_id = step.get("flow_id") if isinstance(step, dict) else None
        try:
            return await self._advance_flow(token, handler, queues, status, step)
        except SeedError:
            if flow_id:
                try:
                    await self.rest("DELETE", "/api/config/config_entries/flow/%s" % flow_id, token=token)
                except SeedError as err:  # best effort; the original error is the one that matters
                    _LOGGER.debug("could not abort flow %s: %s", flow_id, err)
            raise

    async def _advance_flow(
        self, token: str, handler: str, queues: dict[str, Any], status: int, step: Any
    ) -> dict:
        while True:
            if status != 200 or not isinstance(step, dict):
                raise SeedError("flow", "config flow %s failed (HTTP %s): %s" % (handler, status, step))
            kind = step.get("type")
            if kind == "create_entry":
                return step
            if kind == "abort":
                raise SeedError("flow_abort", "config flow %s aborted: %s" % (handler, step.get("reason")))
            if kind not in ("form", "menu"):
                raise SeedError("flow", "config flow %s reached unsupported step type %s" % (handler, kind))
            if step.get("errors"):
                raise SeedError(
                    "flow_errors",
                    "config flow %s step %s returned errors: %s"
                    % (handler, step.get("step_id"), step["errors"]),
                )
            step_id = step.get("step_id", "")
            if step_id not in queues:
                raise SeedError(
                    "flow_step",
                    "config flow %s has no answer for step %r" % (handler, step_id),
                )
            answer = queues[step_id]
            if isinstance(answer, list):
                if not answer:
                    raise SeedError(
                        "flow_step",
                        "config flow %s step %r was shown more often than answered" % (handler, step_id),
                    )
                answer = answer.pop(0)
            elif callable(answer):
                answer = answer(step)
            status, step = await self.rest(
                "POST",
                "/api/config/config_entries/flow/%s" % step["flow_id"],
                json=answer,
                token=token,
            )
