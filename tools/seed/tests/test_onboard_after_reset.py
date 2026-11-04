"""After a reset the stored credentials outlive the wiped instance (PREV-06, D-27).

Home Assistant answers 404 on /api/onboarding for a moment after it starts, before the onboarding
views exist. With credentials already stored that must not be read as "already onboarded":
onboard_if_needed has to keep asking until the onboarding steps appear, then onboard again with the
same stored login.

Run: python -B -m unittest discover -s tools/seed/tests -t . -p 'test_*.py' -v
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from unittest import mock

from tools.seed import bootstrap
from tools.seed.client import SeedError
from tools.seed.creds import CredentialStore

OPEN_STEPS = [
    {"step": "user", "done": False},
    {"step": "core_config", "done": False},
    {"step": "analytics", "done": False},
    {"step": "integration", "done": False},
]


class FakeClient:
    """Answers /api/onboarding from a script; a login works only when ``login_ok``."""

    client_id = "https://127.0.0.1:1/"

    def __init__(self, onboarding_answers: list[int], login_ok: bool) -> None:
        self.answers = list(onboarding_answers)
        self.login_ok = login_ok
        self.calls: list[str] = []
        self.logins = 0

    async def rest(self, method: str, path: str, json=None, data=None, token=None):
        self.calls.append("%s %s" % (method, path))
        if (method, path) == ("GET", "/api/onboarding"):
            status = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
            return status, (OPEN_STEPS if status == 200 else None)
        if (method, path) == ("POST", "/api/onboarding/users"):
            return 200, {"auth_code": "code"}
        return 200, {}

    async def login(self, username: str, password: str) -> str:
        self.logins += 1
        if not self.login_ok:
            raise SeedError("auth", "login as %s failed" % username)
        return "token"

    async def exchange_code(self, code: str) -> str:
        return "token"


class OnboardAfterResetTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.creds = CredentialStore(self._tmp.name, "preview")
        self.creds.admin()  # stored credentials from before the reset
        self.sleeps: list[float] = []

        async def no_sleep(seconds: float) -> None:
            self.sleeps.append(seconds)

        patcher = mock.patch.object(bootstrap.asyncio, "sleep", no_sleep)
        patcher.start()
        self.addCleanup(patcher.stop)

    def onboard(self, client: FakeClient):
        return asyncio.run(bootstrap.onboard_if_needed(client, self.creds, "en", lambda _line: None))

    def test_a_404_with_stored_credentials_that_do_not_log_in_waits_for_onboarding_and_onboards(self) -> None:
        client = FakeClient([404, 404, 404, 200], login_ok=False)
        result = self.onboard(client)
        self.assertTrue(result.onboarded)
        self.assertIn("POST /api/onboarding/users", client.calls)
        self.assertGreaterEqual(client.calls.count("GET /api/onboarding"), 4)

    def test_a_404_with_stored_credentials_that_log_in_means_already_onboarded(self) -> None:
        client = FakeClient([404], login_ok=True)
        result = self.onboard(client)
        self.assertFalse(result.onboarded)
        self.assertEqual(client.calls, ["GET /api/onboarding"])
        self.assertEqual(client.logins, 1)

    def test_a_brand_new_tool_still_waits_without_trying_a_login(self) -> None:
        os.remove(self.creds.path)
        fresh = CredentialStore(self._tmp.name, "preview")
        client = FakeClient([404, 200], login_ok=False)
        result = asyncio.run(bootstrap.onboard_if_needed(client, fresh, "en", lambda _line: None))
        self.assertTrue(result.onboarded)
        self.assertEqual(client.logins, 0)


if __name__ == "__main__":
    unittest.main()
