---
last_mapped_commit: f811e9172bf425ade1c9580c6de2b1b0ef0637ee
last_mapped_at: 2026-10-26
---
# Testing Patterns

**Analysis Date:** 2026-10-26

## Current State (read first)

**No test files are present in this repository.** A search of the working tree (excluding `.claude/`) and of all git history for `test_*.py`, `test_*.js`, and `conftest.py` returned nothing. No `pytest.ini`, `pyproject.toml`, `setup.cfg`, `package.json` test script, or CI test job exists. `.github/workflows/deploy-docs.yml` only builds the documentation site.

`PROJECT_CONTEXT.md` (lines 13, 90-111, 165) describes a suite of about 20 Python `test_*.py` files and 37 jsdom `test_*.js` files, run via `python3 -m pytest test_*.py -q` and `node`. Those files are not in this checkout, and the document itself notes that several were removed. Treat the instructions there as historical and unverifiable from this repo. Do not assume the suite exists, and do not cite its pass counts as current.

The `.gitignore` lists `.pytest_cache/`, so pytest was run at some point, but no test artifacts are committed.

## Test Framework

**Intended runners (per `PROJECT_CONTEXT.md`, not present in repo):**
- Python: `pytest` (run as `python3 -m pytest test_*.py -q`). Each test file was also written as a standalone script with an `asyncio.run(...)` entry point.
- JavaScript: plain Node scripts using `jsdom` (`require()` of a `node_modules` path), run per file with `node test_<name>.js`.

**Assertion:**
- Python: the historical suite used a local `check(cond, msg)` helper rather than bare `assert`. Standard `assert` is fine for new tests under pytest.
- JavaScript: plain `console`/`throw`-based checks inside each file.

**Run commands (for when tests are added):**

```bash
python3 -m pytest tests/ -q                 # Python engine and websocket tests (once a tests/ dir exists)
node tests/js/test_<name>.js                # Single card test under jsdom (after npm install jsdom)
```

There is no coverage tool configured. No watch mode is configured.

## Test File Organization

**Location:** Not established. No `tests/` directory or co-located test files exist.

**Naming (historical, from `PROJECT_CONTEXT.md`):** `test_<feature>.py` and `test_<feature>.js`, e.g. `test_grocy_recipe_importer.js`, `test_rewards_card.js`, `test_reward_engine.py`, `test_chores_websocket_api.py`, `test_my_chores_card.js`.

**Recommended structure for new tests:**

```
tests/
  test_chore_engine.py          # pure engine logic, no hass
  test_reward_engine.py
  test_pantry_engine.py
  test_chores_websocket_api.py  # uses fake hass + recording connection
  js/
    test_rewards_card.js        # jsdom, loads card source
```

This mirrors the module split in `custom_components/family_hub/` (engines versus websocket handlers) and keeps the pure engines testable without Home Assistant installed.

## Test Structure

**Suite organization (historical pattern to follow):**

```python
import asyncio

def check(cond, msg):
    if not cond:
        raise AssertionError(msg)

async def run():
    ...

if __name__ == "__main__":
    asyncio.run(run())
```

Key rule recorded in `PROJECT_CONTEXT.md`: never call `asyncio.run(...)` at module level. Guard it with `if __name__ == "__main__":`, otherwise pytest collection breaks for every file collected afterward. Set `__test__ = False` on any file that must stay a standalone script and not be collected.

**Patterns for new tests:**
- Use `pytest` functions and `pytest.mark.asyncio` (or `asyncio.run` inside a sync test) for coroutine-based websocket handlers.
- Build records with the `default_<thing>()` factories from the engine modules (e.g. `default_pantry_extra` in `custom_components/family_hub/pantry_engine.py`) and override only the fields under test.
- Assert on the error `code` attribute (`PantryError.code`, `ChoreError.code`) rather than on message text. Message wording changes; codes are the contract.

## Mocking

**Home Assistant:** Real Home Assistant is not installed in the test environment. The historical approach was a hand-built fake `homeassistant` package with stub modules for `homeassistant.core`, `homeassistant.config_entries`, `homeassistant.components.websocket_api`, `homeassistant.helpers.storage`, `homeassistant.util.dt`, and similar. Keep stubs minimal and only as complete as the code under test requires. Put the fake package in the test tree (e.g. `tests/fakes/homeassistant/`) rather than `/tmp`, so it survives sessions.

**Websocket connection:** Use a recording fake that stores calls to `send_result`, `send_error`, and `send_message` so tests can assert on the outbound payload and error code.

**Services and bus:** Replace `hass.services.async_call` and `hass.bus.async_fire` with recording fakes. Assert on the recorded call list. The historical `test_chores_websocket_api.py` recorded service calls this way for notification tests.

**Grocy HTTP:** Replace the aiohttp session with a fake session class and a fake JSON response object that returns canned payloads. Pattern: `FakeSession`, `FakeGetSession`, `FakeJsonGetResponse`, defined locally in each test file.

**Frontend (jsdom):** Load the card source into a jsdom window, define `customElements`, and instantiate the element. Assert on rendered DOM and on the websocket commands the card sends. Do not depend on real image decoding; stub it.

**What to Mock:**
- The `hass` object and its `services`, `bus`, `data`, and `auth` attributes.
- The websocket `connection` object (user with `is_admin`, `send_result`, `send_error`).
- Grocy and any other external HTTP.
- Time, when a test depends on `dt_util.now()` or the recurring-chore clock.

**What NOT to Mock:**
- The engine modules themselves. Test `chore_engine`, `reward_engine`, and the other `*_engine.py` modules directly with real dicts. They are pure Python and need no mocks.
- The state machine transitions in `chore_engine.py`. Exercise them end to end on a real record.
- Permission checks in websocket handlers. Use a user fake with `is_admin` set both ways.

## Fixtures and Factories

**Test data:**
- Use the engine `default_*` factories and `new_*_id` helpers. Example from `custom_components/family_hub/pantry_engine.py`: `default_pantry_extra(**overrides)` returns a fully populated record.
- Store fixtures are plain dicts keyed by ID, for example `extras: dict[str, dict[str, Any]]` in `pantry_engine.py`. Build them inline in the test.

**Location:** None exists. Put shared fixtures in `tests/conftest.py` once pytest is adopted, and keep JS fixtures next to the JS test files.

## Coverage

**Requirements:** None enforced. No coverage configuration or threshold exists.

**View Coverage:** Not configured. To measure once `pytest-cov` is added:

```bash
python3 -m pytest tests/ --cov=custom_components/family_hub --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Target: the `*_engine.py` modules and `const.py` helpers. These are the highest-value, lowest-cost tests because they have no Home Assistant dependency.
- Verify the state machine in `chore_engine.py` (open, pending_verification, approved, recurring reset), dependency resolution, overdue penalties, and reward balance math.

**Integration Tests:**
- Target: the `*_websocket_api.py` handlers with a fake `hass` and a recording connection. Verify permission gating (`forbidden`), not-found handling, and that exactly one `async_save` occurs per call.
- Notification side effects (`_notify_reward_claimed`, `_notify_chore_approved`) belong here, asserted via the recording service fake.

**Frontend Tests:**
- Target: card rendering and websocket call wiring in `custom_components/family_hub/card/*.js`. Use jsdom. Cover admin-only controls (render only when `_isAdmin()`), default states, and the exact payload sent on Add/Update/Delete.
- Regression guards may be plain source-text assertions (a regex over the card file) when jsdom cannot apply the card's own `<style>` block to `getComputedStyle`.

**E2E Tests:**
- Not used. No Home Assistant instance or browser E2E harness is configured.

## Common Patterns

**Async testing (Python):**

```python
import asyncio

def test_reward_claim_notifies_all_opted_in_profiles():
    async def scenario():
        ...
    asyncio.run(scenario())
```

Or with `pytest-asyncio`, mark the test `@pytest.mark.asyncio` if that plugin is added.

**Error testing (Python engine):**

```python
import pytest
from custom_components.family_hub.pantry_engine import PantryError, create_extra

def test_create_extra_requires_name():
    with pytest.raises(PantryError) as exc:
        create_extra({}, {"name": ""})
    assert exc.value.code == "invalid_name"
```

**Error testing (websocket handler):**

```python
def test_locked_set_forbidden_for_non_admin(conn_non_admin):
    handler_call(conn_non_admin, {"item_id": "x", "content": {}})
    assert conn_non_admin.errors[-1] == ("forbidden", ...)
```

Assert on the recorded error code, not on the human-readable sentence.

---

*Testing analysis: 2026-10-26*
