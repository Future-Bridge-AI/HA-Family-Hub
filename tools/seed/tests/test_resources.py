"""resources-sync: served files, the cache-busting hash, the update plan and the sync loop."""
from __future__ import annotations

import asyncio
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.seed.client import SeedError
from tools.seed.resources import content_hash, plan_updates, served_js_files, served_urls, sync

INTEGRATION = Path(__file__).resolve().parents[3] / "custom_components" / "family_hub"


class ServedFilesTests(unittest.TestCase):
    def test_lists_the_twelve_cards_and_two_panel_files(self) -> None:
        files = served_js_files(str(INTEGRATION))
        self.assertEqual(len(files), 14)
        self.assertEqual(len([p for p in files.values() if "/card/" in p]), 12)
        self.assertEqual(len([p for p in files.values() if "/panel/" in p]), 2)
        for name in ("family-week-calendar-card.js", "theme-selector-card.js", "theme-builder-panel.js"):
            self.assertIn(name, files)

    def test_served_urls_are_read_from_const(self) -> None:
        urls = served_urls(str(INTEGRATION))
        self.assertEqual(len(urls), 14)
        self.assertEqual(
            urls["family-week-calendar-card.js"], "/family_hub_card/family-week-calendar-card.js"
        )
        self.assertEqual(urls["theme-builder-panel.js"], "/family_hub_panel/theme-builder-panel.js")


class ContentHashTests(unittest.TestCase):
    def test_matches_the_integrations_own_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.js"
            path.write_bytes(b"console.info('hello');\n")
            expected = hashlib.sha256(b"console.info('hello');\n").hexdigest()[:10]
            self.assertEqual(content_hash(str(path)), expected)
            self.assertEqual(len(content_hash(str(path))), 10)


class PlanUpdatesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.files = {}
        for name, body in (("a-card.js", b"A"), ("b-card.js", b"B"), ("p-panel.js", b"P")):
            path = root / name
            path.write_bytes(body)
            self.files[name] = str(path)
        self.urls = {
            "a-card.js": "/x_card/a-card.js",
            "b-card.js": "/y_card/b-card.js",
            "p-panel.js": "/z_panel/p-panel.js",
        }

    def hash_of(self, name: str) -> str:
        return content_hash(self.files[name])

    def test_changed_hash_is_an_update(self) -> None:
        resources = [{"id": "r1", "type": "module", "url": "/x_card/a-card.js?v=0000000000"}]
        plan = plan_updates(resources, {"a-card.js": self.files["a-card.js"]}, self.urls)
        self.assertEqual(
            plan,
            [
                {
                    "action": "update",
                    "resource_id": "r1",
                    "url": "/x_card/a-card.js?v=" + self.hash_of("a-card.js"),
                    "old_url": "/x_card/a-card.js?v=0000000000",
                }
            ],
        )

    def test_unchanged_hash_is_nothing(self) -> None:
        resources = [{"id": "r1", "type": "module", "url": "/x_card/a-card.js?v=" + self.hash_of("a-card.js")}]
        self.assertEqual(plan_updates(resources, {"a-card.js": self.files["a-card.js"]}, self.urls), [])

    def test_served_card_without_a_resource_is_a_create(self) -> None:
        plan = plan_updates([], {"b-card.js": self.files["b-card.js"]}, self.urls)
        self.assertEqual(
            plan, [{"action": "create", "url": "/y_card/b-card.js?v=" + self.hash_of("b-card.js")}]
        )

    def test_panel_file_never_gets_a_resource(self) -> None:
        self.assertEqual(plan_updates([], {"p-panel.js": self.files["p-panel.js"]}, self.urls), [])

    def test_two_resources_for_one_path_is_a_duplicate_error_and_never_a_create(self) -> None:
        resources = [
            {"id": "r1", "type": "module", "url": "/x_card/a-card.js?v=1111111111"},
            {"id": "r2", "type": "module", "url": "/x_card/a-card.js?v=2222222222"},
        ]
        plan = plan_updates(resources, {"a-card.js": self.files["a-card.js"]}, self.urls)
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["action"], "duplicate")
        self.assertEqual(plan[0]["resource_ids"], ["r1", "r2"])

    def test_resources_that_are_not_served_files_are_left_alone(self) -> None:
        resources = [{"id": "r9", "type": "module", "url": "/somewhere/else-card.js?v=123"}]
        self.assertEqual(plan_updates(resources, {"a-card.js": self.files["a-card.js"]}, {}), [])


class FakeWebSocket:
    """Stands in for the lovelace resources websocket API, with an optional mid-run failure."""

    def __init__(self, resources: list, fail_on_update: int = 0) -> None:
        self.resources = resources
        self.updates = 0
        self.fail_on_update = fail_on_update
        self._next = 100

    async def call(self, type: str, **fields):
        if type == "lovelace/resources":
            return {"result": [dict(item) for item in self.resources]}
        if type == "lovelace/resources/update":
            self.updates += 1
            if self.fail_on_update and self.updates == self.fail_on_update:
                raise SeedError("interrupted", "simulated interruption")
            for item in self.resources:
                if item["id"] == fields["resource_id"]:
                    item["url"] = fields["url"]
            return {"result": {}}
        if type == "lovelace/resources/create":
            self._next += 1
            self.resources.append({"id": "r%d" % self._next, "type": fields["res_type"], "url": fields["url"]})
            return {"result": {}}
        raise AssertionError("unexpected call %s" % type)


class FakeClient:
    def __init__(self, sock: FakeWebSocket) -> None:
        self.sock = sock

    async def ws(self, token: str) -> FakeWebSocket:
        return self.sock


class SyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "family_hub"
        for rel, body in (
            ("card/one-card.js", b"1"),
            ("card/two-card.js", b"2"),
            ("card/three-card.js", b"3"),
            ("panel/main-panel.js", b"p"),
        ):
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_bytes(body)
        (self.root / "const.py").write_text(
            'A_JS_URL = "/f_one/one-card.js"\n'
            'B_JS_URL = "/f_two/two-card.js"\n'
            'C_JS_URL = "/f_three/three-card.js"\n'
            'PANEL_JS_URL = "/f_panel/main-panel.js"\n',
            encoding="utf-8",
        )

    def run_sync(self, sock: FakeWebSocket, apply: bool = True) -> dict:
        lines: list = []
        counts = asyncio.run(sync(FakeClient(sock), "token", str(self.root), apply, say=lines.append))
        counts["lines"] = lines
        return counts

    def paths(self, sock: FakeWebSocket) -> list:
        return sorted(item["url"].split("?", 1)[0] for item in sock.resources)

    def assert_one_row_per_path_with_current_hash(self, sock: FakeWebSocket) -> None:
        self.assertEqual(
            self.paths(sock), ["/f_one/one-card.js", "/f_three/three-card.js", "/f_two/two-card.js"]
        )
        for item in sock.resources:
            name = item["url"].split("?", 1)[0].rsplit("/", 1)[1]
            rel = "card/" + name
            self.assertTrue(item["url"].endswith("?v=" + content_hash(str(self.root / rel))), item["url"])

    def test_second_run_reports_zero_updates(self) -> None:
        sock = FakeWebSocket([{"id": "r1", "type": "module", "url": "/f_one/one-card.js?v=0000000000"}])
        first = self.run_sync(sock)
        self.assertEqual((first["updated"], first["created"]), (1, 2))
        self.assertIn("resources: 1 updated, 2 created, 0 unchanged", first["lines"])
        second = self.run_sync(sock)
        self.assertEqual((second["updated"], second["created"]), (0, 0))
        self.assertIn("resources: 0 updated, 0 created, 3 unchanged", second["lines"])
        self.assert_one_row_per_path_with_current_hash(sock)

    def test_an_interrupted_run_is_finished_by_the_next_one_without_duplicates(self) -> None:
        sock = FakeWebSocket(
            [
                {"id": "r1", "type": "module", "url": "/f_one/one-card.js?v=1"},
                {"id": "r2", "type": "module", "url": "/f_two/two-card.js?v=2"},
                {"id": "r3", "type": "module", "url": "/f_three/three-card.js?v=3"},
            ],
            fail_on_update=2,
        )
        with self.assertRaises(SeedError):
            self.run_sync(sock)
        again = self.run_sync(sock)
        self.assertEqual(again["created"], 0)
        self.assertEqual(self.run_sync(sock)["updated"], 0)
        self.assert_one_row_per_path_with_current_hash(sock)

    def test_dry_run_changes_nothing(self) -> None:
        sock = FakeWebSocket([{"id": "r1", "type": "module", "url": "/f_one/one-card.js?v=0000000000"}])
        counts = self.run_sync(sock, apply=False)
        self.assertEqual((counts["updated"], counts["created"]), (1, 2))
        self.assertEqual(sock.updates, 0)
        self.assertEqual(len(sock.resources), 1)

    def test_a_duplicate_path_stops_the_sync_before_any_write(self) -> None:
        sock = FakeWebSocket(
            [
                {"id": "r1", "type": "module", "url": "/f_one/one-card.js?v=1"},
                {"id": "r2", "type": "module", "url": "/f_one/one-card.js?v=2"},
            ]
        )
        with self.assertRaises(SeedError) as caught:
            self.run_sync(sock)
        self.assertEqual(caught.exception.code, "duplicate")
        self.assertEqual(sock.updates, 0)
        self.assertEqual(len(sock.resources), 2)


if __name__ == "__main__":
    unittest.main()
