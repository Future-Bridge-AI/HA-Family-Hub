"""Invariants of the environment table: nothing may be shared between Dev and Preview."""
from __future__ import annotations

import dataclasses
import re
import unittest

from tools.seed.envs import ENVIRONMENTS, Env, GuardRefused, base_url, get_env

IDENTITY_WORD = re.compile(r"\b(PREVIEW|DEV)\b")


class EnvironmentTableTests(unittest.TestCase):
    def test_only_dev_and_preview_exist(self) -> None:
        self.assertEqual(sorted(ENVIRONMENTS), ["dev", "preview"])
        for refused in ("home", "prod", ""):
            with self.assertRaises(GuardRefused):
                get_env(refused)

    def test_every_field_differs_between_environments(self) -> None:
        dev, preview = ENVIRONMENTS["dev"], ENVIRONMENTS["preview"]
        for field in dataclasses.fields(Env):
            self.assertNotEqual(
                getattr(dev, field.name), getattr(preview, field.name), "field %s is shared" % field.name
            )

    def test_tags_are_bracketed_upper_case_with_one_trailing_space(self) -> None:
        for env in ENVIRONMENTS.values():
            self.assertRegex(env.tag, r"^\[[A-Z]+\] $")
            self.assertTrue(env.marker_prefix.startswith("family-hub-seed:"))
            self.assertTrue(env.marker_prefix.endswith(":"))

    def test_location_name_and_dashboard_title_carry_the_identity_word_once(self) -> None:
        for env in ENVIRONMENTS.values():
            for text in (env.location_name, env.dashboard_title):
                self.assertEqual(len(IDENTITY_WORD.findall(text)), 1, text)
                # a lower-case or mixed-case spelling must not also be present
                self.assertEqual(len(re.findall(r"\b(PREVIEW|DEV)\b", text, flags=re.I)), 1, text)

    def test_themes_are_distinct_from_each_other_and_from_the_default(self) -> None:
        self.assertEqual(ENVIRONMENTS["preview"].theme, "midnight")
        self.assertEqual(ENVIRONMENTS["dev"].theme, "blossom")
        for env in ENVIRONMENTS.values():
            self.assertNotEqual(env.theme, "slate")


class BaseUrlGuardTests(unittest.TestCase):
    def test_default_is_https_on_loopback(self) -> None:
        self.assertEqual(base_url(ENVIRONMENTS["dev"]), "https://127.0.0.1:8130")
        self.assertEqual(base_url(ENVIRONMENTS["preview"]), "https://127.0.0.1:8124")

    def test_loopback_overrides_are_accepted(self) -> None:
        env = ENVIRONMENTS["dev"]
        for url in ("https://127.0.0.1:18130", "https://localhost:8130", "https://[::1]:8130"):
            self.assertEqual(base_url(env, url), url)

    def test_everything_else_is_refused(self) -> None:
        env = ENVIRONMENTS["dev"]
        for url in (
            "http://127.0.0.1:8130",
            "https://192.0.2.1:8130",
            "https://example.com",
            "https://127.0.0.1.nip.io:8130",
            "127.0.0.1:8130",
            "https://user:pw@127.0.0.1:8130",
        ):
            with self.subTest(url=url):
                with self.assertRaises(GuardRefused):
                    base_url(env, url)

    def test_refusal_names_the_loopback_rule(self) -> None:
        with self.assertRaises(GuardRefused) as caught:
            base_url(ENVIRONMENTS["dev"], "https://192.0.2.10:8130")
        self.assertIn("loopback", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
