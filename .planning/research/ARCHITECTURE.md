# Architecture Research

**Domain:** Environment, deploy, seed, test and release architecture around an existing Home Assistant custom integration (brownfield fork, `family_hub`, Dev / Family Preview / Home)
**Researched:** 2026-10-26
**Confidence:** MEDIUM-HIGH (HA onboarding/auth/Docker/HACS mechanics verified against official sources or HA source; sizing, Companion-app and Tailscale behaviour are from training knowledge and flagged MEDIUM)

> Scope note: this document does NOT re-describe the integration's internal architecture (see `.planning/codebase/ARCHITECTURE.md`). It describes what must be built *around* it, how that scaffolding talks to the integration, and in what order to build it.

---

## Standard Architecture

### System Overview

Three Home Assistant instances run the same integration code at different trust levels. They share **nothing at runtime** (no volume, no network route, no credentials, no calendars). They share only **code (git)** and **seed data definitions (git)**.

```
                       GitHub: Future-Bridge-AI/HA-Family-Hub
        ┌──────────────────────────────────────────────────────────────┐
        │  custom_components/family_hub/   tools/seed/   dev/   tests/  │
        │  .github/workflows (CI + release)   docs/family/              │
        └───────┬───────────────────┬──────────────────────┬───────────┘
   working copy │            git ref│(branch or sha)       │ tag vX.Y.Z -> GitHub Release
                ▼                   ▼                      ▼
┌───────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────────┐
│ DEV (developer laptop)│ │ FAMILY PREVIEW           │ │ HOME (production)            │
│ docker compose        │ │ (always-on LAN box)      │ │ existing family HA           │
│  HA container :8130   │ │ docker compose           │ │  HACS custom repository      │
│  bind-mount of working│ │  HA container :8124      │ │  (release tag, NOT branch)   │
│  copy (live edit)     │ │  rsync'd copy of a ref   │ │  real calendars/lists/notify │
│  throwaway config vol │ │  own config vol, own net │ │  family data in .storage     │
│  seed: yes, any time  │ │  seed: scripted, reset   │ │  seed: NEVER                 │
│  data: demo           │ │  data: pretend family    │ │  data: real                  │
└──────────▲────────────┘ └────────▲─────────────────┘ └──────────────▲───────────────┘
           │ tools/seed (HTTP+WS)  │ tools/seed (HTTP+WS)             │ sign-off gate
           │                       │                                  │ (her UAT in Preview)
           │                       └─── she uses it: tablet/phone ────┘
           │
┌──────────┴────────────────────────────────────────────────────────────────────────────┐
│ CI (GitHub Actions, no HA instance): ruff · hassfest · HACS validate · pytest (engines,│
│ ws, setup smoke) · Playwright card smoke on mocked hass · guard checks                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Integration package** (`custom_components/family_hub/`) | The only deployable artefact. Unchanged contract: HA loads the folder. | Existing code; new work lands in new modules (see Extraction) |
| **Env definitions** (`dev/`) | Describe *how an HA instance is run*: pinned image, ports, config template, per-env overlays | One base `compose.yaml` + `compose.dev.yaml` + `compose.preview.yaml`, `.env.example`, `config-template/` |
| **Instance bootstrap / onboarding** (`tools/seed/onboard.py`) | Take a *fresh, empty* HA config volume to "onboarded owner + token" without a human clicking | HA onboarding REST API -> auth code -> token -> long-lived token; idempotent |
| **Seed engine** (`tools/seed/`) | Make an onboarded HA look like "our family, this week" using only public HA APIs plus Family Hub's own commands | Python (`aiohttp`) client + declarative YAML data with date offsets |
| **Seed data** (`tools/seed/data/*.yaml`) | Single source of truth for the pretend family (members, users, calendars, events, meals, chores, rewards) | Declarative, relative dates (`+0d 17:30`), never absolute |
| **Deploy tool** (`scripts/deploy-preview`) | Put exactly one git ref's `custom_components/family_hub` into Preview and restart it | git ref -> `git archive` / `rsync --delete` -> `docker compose restart` -> wait healthy -> record build marker |
| **Reset tool** (`scripts/reset-preview`, `scripts/dev-reset`) | Return an instance to known-good seeded state | stop -> wipe config volume (including `family_hub_backups/`) -> start -> onboard -> seed |
| **Python test suite** (`tests/python/`) | Pure-engine tests, websocket/store tests, setup-smoke test | `pytest` + `pytest-homeassistant-custom-component` |
| **JS test suite** (`tests/js/`) | Load each served card module against a mocked `hass`; also produce screenshots | Playwright (Chromium) with a static harness page, mocked `hass.callWS` and `fetch` |
| **E2E / screenshot runner** (`tests/e2e/`) | Drive a *real* Dev/Preview HA to take before/after pictures for her | Playwright with token injected into `localStorage` |
| **CI** (`.github/workflows/ci.yml`) | Gate every PR: lint, validation, unit, card smoke, guards | GitHub Actions; no HA instance needed |
| **Release pipeline** (`.github/workflows/release.yml`) | Turn a signed-off commit into a HACS-installable release | Tag `vX.Y.Z` -> verify manifest==tag -> re-run CI -> GitHub Release with notes |
| **Family docs** (`docs/family/`) | Plain-language guide and `whats-new.md`; screenshots generated by the E2E runner | Markdown |

---

## Recommended Project Structure

```
HA-Family-Hub/
├── custom_components/family_hub/        # the integration (ONLY this ships)
│   ├── frontend.py                      # NEW (extraction #1): card/panel table, static paths, resource registration
│   ├── <feature>_engine.py              # pure logic            (existing pattern)
│   ├── <feature>_websocket_api.py       # ws commands + async_register(hass)  (existing pattern)
│   ├── card/  panel/                    # the only served JS
│   └── ...
├── dev/                                 # "how HA runs" - no Python app code here
│   ├── compose.yaml                     # base: pinned HA image, tz, volume
│   ├── compose.dev.yaml                 # bind-mount working copy, port 8130, debug logging
│   ├── compose.preview.yaml             # restart: unless-stopped, port 8124, no source bind-mount
│   ├── .env.example                     # HA_IMAGE_TAG, ports, PREVIEW_HOST (never real secrets)
│   └── config-template/                 # configuration.yaml, themes/, dashboards/*.yaml (version-controlled)
├── tools/seed/                          # Python, stdlib + aiohttp only
│   ├── ha_client.py                     # REST + websocket wrapper
│   ├── onboard.py                       # fresh volume -> owner user -> long-lived token
│   ├── seed_ha.py                       # users, persons, local calendars/todos, events via services
│   ├── seed_family_hub.py               # config flow + Family Hub chores/rewards/meals via ITS commands
│   ├── cli.py                           # `seed --target dev|preview [--refresh|--reset]`
│   └── data/                            # family.yaml, calendars.yaml, week.yaml, chores.yaml, ...
├── scripts/                             # thin wrappers only; logic lives in tools/
│   ├── dev-up  dev-reset
│   ├── deploy-preview  reset-preview  preview-refresh
│   └── check-guards                     # repo guard checks (see CI)
├── tests/
│   ├── python/
│   │   ├── conftest.py                  # pytest_plugins = "pytest_homeassistant_custom_component"
│   │   ├── engines/                     # no hass fixture - plain dict in, dict out
│   │   ├── api/                         # hass + hass_ws_client + MockConfigEntry
│   │   ├── smoke/                       # setup_entry loads; N ws commands; statics served; services registered
│   │   ├── fixtures/storage/v<N>/       # frozen old-schema Store payloads for migration tests
│   │   └── ws_commands.json             # checked-in contract: every registered family_hub/* command
│   ├── js/
│   │   ├── harness/                     # index.html + mock-hass.js + mock-fetch.js
│   │   ├── fixtures/                    # callWS responses recorded from seeded Dev
│   │   └── smoke/ visual/               # *.spec.ts
│   └── e2e/                             # Playwright against live Dev/Preview (not in PR CI)
├── docs/family/                         # getting-started.md, whats-new.md, img/
└── .github/workflows/                   # ci.yml, validate.yml (hassfest+HACS), release.yml, deploy-docs.yml (existing)
```

### Structure Rationale

- **`dev/` vs `tools/` vs `scripts/`:** `dev/` is declarative environment config (what to run). `tools/` is code with logic and tests (seeding). `scripts/` is one-line entry points so the developer types `scripts/deploy-preview my-branch` and never remembers flags. Keeps logic out of bash.
- **One compose base + overlays:** Dev and Preview run the *same* image tag and same `configuration.yaml`; only mounts, port and restart policy differ. "It worked in Dev but not in Preview" then means code or data, not environment.
- **Seed data outside the integration:** it must not ship to Home. Nothing under `tools/`, `dev/`, `tests/` is inside `custom_components/`, so HACS never delivers it.
- **`tests/` at repo root, not inside the package:** HACS/hassfest ship `custom_components/family_hub/` only; test files in the package would ship to Home.
- **`ws_commands.json` contract file:** the cheapest safety net for refactoring a 13k-line file — extraction cannot silently drop a `family_hub/...` command.

---

## Environment Decisions (recommended, opinionated)

These resolve the "Pending (decide in Preview phase)" rows in PROJECT.md.

| Decision | Recommendation | Why | Confidence |
|----------|---------------|-----|------------|
| Where Preview runs | **An always-on Linux Docker host on the home LAN** (NAS with Container Manager, mini PC, or Pi 4/5 with SSD and 64-bit OS). Not the laptop. Do **not** co-host on the Home HA box. | She needs it available whenever she picks up a tablet; a second HA container idles at a few hundred MB RAM. Co-hosting couples failure/resource domains and, on HA OS, would mean add-on gymnastics. Laptop is acceptable only as a *temporary* bootstrap. | MEDIUM |
| Separate instance? | **Always a separate HA instance**, own container, own config volume, own Docker network, own port (8124), no mounts shared with Home, no Home credentials on the host. | Isolation is the project's Safety constraint. A "preview area/user" inside Home does not isolate integration crashes, storage migrations or restarts. | HIGH (project constraint) |
| Dev location | Developer laptop (or this sandbox), port **8130**, throwaway config volume under `dev/.ha-dev/` (gitignored) | Live bind-mount for edit-restart loop. Distinct port so Dev never collides with a local Home or Preview tab/cookies | HIGH |
| Port allocation | Home 8123 (untouched), Preview **8124**, Dev **8130** | Browser `localStorage` tokens are per-origin (host:port); distinct ports avoid cross-login confusion on shared devices | HIGH |
| Docker networking | Default bridge network + published port (not `network_mode: host`) for Preview and Dev | Two HA instances on host networking would both bind 8123 and fight over discovery. This integration needs no mDNS/discovery. | MEDIUM |
| HA image version | Pin `ghcr.io/home-assistant/home-assistant:<exact tag>` in `.env`, same tag for Dev and Preview, and the **same minor as Home**. Bump Preview first, then Home ("Preview is the HA-upgrade canary"). | Eliminates environment drift; gives a free rehearsal of every HA core upgrade. | HIGH |
| How she reaches Preview | **v1: LAN only**, via a DHCP reservation + router DNS name or mDNS (`http://preview.lan:8124`), HA Companion app added as a **second server**, plus a bookmarked kiosk-dashboard URL on the tablet. **v2 (optional): Tailscale** (`tailscale serve` for HTTPS) if she must use it away from home. **Do not use Nabu Casa for Preview** — a Cloud subscription is per instance and belongs to Home. | LAN-only is the simplest thing that satisfies "feels like an app". Tailscale keeps the no-cloud-backend constraint (peer-to-peer VPN, no hosted app backend). | MEDIUM |
| HTTPS parity | Check whether Home is served over HTTPS (Nabu Casa / reverse proxy). If it is and any card uses secure-context APIs (calendar card has 3 references: wake-lock/clipboard/notification/fullscreen class), serve Preview over HTTPS too (`tailscale serve`, or Caddy), otherwise behaviour differs between Preview and Home. | Secure-context-only browser APIs silently fail on plain `http://ip` | MEDIUM |
| Unmistakable Preview identity | Preview's `homeassistant: name: "Family Hub PREVIEW"`, a distinct accent theme, and a banner/markdown card on every Preview dashboard | The worst failure is her ticking a "real" chore in the wrong instance or the family mistaking Preview for Home | HIGH |
| Safe outbound | Preview has **no** `mobile_app` devices, **no** real notify targets, Grocy disabled. Use the built-in `notify.persistent_notification` as the required `notify.*` target. | Seeded reminders/Daily Digest must never ping real phones | HIGH |

---

## Architectural Patterns

### Pattern 1: Compose base + per-environment overlay

**What:** One `dev/compose.yaml` describes the HA service; `compose.dev.yaml` and `compose.preview.yaml` only add what differs. Selected by a wrapper: `docker compose -f dev/compose.yaml -f dev/compose.<env>.yaml --env-file dev/.env.<env> ...`.
**When to use:** Always here — it is what makes Dev and Preview comparable.
**Trade-offs:** Slightly more files than two standalone compose files; far less drift.

```yaml
# dev/compose.yaml (base)
services:
  ha:
    image: ghcr.io/home-assistant/home-assistant:${HA_IMAGE_TAG}
    environment: { TZ: "${TZ}" }
    volumes:
      - ${CONFIG_DIR}:/config
    ports: ["${HA_PORT}:8123"]
    healthcheck:
      test: ["CMD", "curl", "-fs", "http://localhost:8123/api/onboarding"]  # unauthenticated, works pre- and post-onboarding
      interval: 10s
      retries: 30

# dev/compose.dev.yaml
services:
  ha:
    volumes:
      - ../custom_components/family_hub:/config/custom_components/family_hub   # live working copy

# dev/compose.preview.yaml
services:
  ha:
    restart: unless-stopped     # code arrives via deploy-preview rsync, NOT a bind-mount of a mutable checkout
```

### Pattern 2: Pull a ref, copy, restart (deploy-from-branch)

**What:** The Preview host keeps a bare-ish clone of the repo. `deploy-preview <ref>` (run from the developer machine over SSH, or on the host) does `git fetch` -> export the ref (`git archive <ref> custom_components/family_hub` or a detached worktree) -> `rsync -a --delete` into `<preview-config>/custom_components/family_hub/` -> `docker compose restart ha` -> poll `/api/onboarding` until 200 -> record `ref@sha` (and, post-start, publish it as a state so a Preview-only dashboard card can show "Preview build: feature-x @ a1b2c3").
**When to use:** Every Preview deployment.
**Trade-offs:** `rsync --delete` guarantees no stale files (removed modules, old `.js`) survive — directly addressing the stale-duplicate-file problem. Copying (not bind-mounting the clone) means a `git checkout` on the host can never change code under a running HA.

```bash
# scripts/deploy-preview (sketch)
REF="${1:?usage: deploy-preview <branch|sha>}"
ssh "$PREVIEW_HOST" "cd $REPO && git fetch --prune origin && git checkout --detach origin/$REF 2>/dev/null || git checkout --detach $REF"
ssh "$PREVIEW_HOST" "rsync -a --delete --exclude '__pycache__' $REPO/custom_components/family_hub/ $CONFIG/custom_components/family_hub/"
ssh "$PREVIEW_HOST" "cd $REPO/dev && docker compose -f compose.yaml -f compose.preview.yaml restart ha"
tools/seed/cli.py wait-healthy --target preview && tools/seed/cli.py stamp --target preview --ref "$REF"
```

### Pattern 3: API-driven, idempotent, date-relative seeding (with reset = wipe + reseed)

**What:** Seeding talks to a *running* HA through supported interfaces, never by hand-editing `.storage` while HA runs.
1. **Onboard** (fresh volume only): `POST /api/onboarding/users` (name, username, password, client_id, language) -> `auth_code` -> `POST /auth/token` -> access token; then complete the remaining onboarding steps (`core_config`, `analytics`, `integration` with `client_id`/`redirect_uri`) so the "welcome" wizard never appears for her. Then websocket `auth/long_lived_access_token` for a stored seeding token (kept in a gitignored `.env.<target>`, never committed).
2. **HA objects:** websocket `config/auth/create` + `config/auth_provider/homeassistant/create` (family users; hers non-admin), `person/create`, areas. REST `config/config_entries/flow` to add **Local Calendar** (one per member) and **Local To-do** (each list Family Hub needs: recipe box, meal plan, templates, suggestions, reminders, shopping). Events via `calendar.create_event` service; to-do items via `todo.add_item`.
3. **Family Hub entry:** drive its config flow (`user -> features -> users -> member_profile -> chores_features -> calendars -> grocy -> notifications -> digest -> dashboard -> finish`) through `/api/config/config_entries/flow`, answering with seed data (member -> user id -> calendar entity mapping, `notify.persistent_notification`, Grocy skipped).
4. **Family Hub data:** chores, rewards, goals, routines, meals, PINs created by calling the integration's **own `family_hub/...` websocket commands and `family_hub.*` services** — not by writing its Store files.
5. **Dashboards:** the integration explicitly cannot create a dashboard itself (config_flow docstring: it only emits YAML). Create the Family Hub dashboard from the seeder (`lovelace/dashboards/create` + `lovelace/config/save`) **or** declare it as a YAML-mode dashboard in `config-template/` while leaving root `lovelace.mode` as storage so the integration's resource auto-registration (storage-mode only) still works. Spike which one first (see Gaps).

All dates are expressed as offsets from "today" in `tools/seed/data/*.yaml`, resolved at seed time. A `preview-refresh` command re-creates only the event layer so the week never goes stale.

**When to use:** Dev (any time), Preview (initial + weekly refresh + on reset).
**Trade-offs:** Slower than restoring a snapshot (tens of seconds to a couple of minutes) but survives HA and integration schema changes, exercises the real code paths (the seed doubles as a smoke test), and has no secrets in git. A "golden snapshot" tarball of an already-seeded config volume may be added later **as a local, gitignored speed cache only**.

### Pattern 4: One seed definition feeds three consumers

**What:** `tools/seed/data/*.yaml` -> (a) Dev/Preview seeding, (b) recorded JS fixtures (run seed against Dev, capture `callWS` responses with a recorder script, commit them to `tests/js/fixtures/`), (c) Python test factories (engine tests build the same "Mia, 9, has 3 chores" world from the same YAML loader).
**When to use:** From the moment seed data exists.
**Trade-offs:** Couples tests to seed shape (acceptable; one family, one shape). Prevents three divergent hand-made demo worlds.

### Pattern 5: Strangler extraction (new work never grows the monoliths)

**What:** The integration already has the right seam: `*_engine.py` (pure) + `*_websocket_api.py` (HA-facing, owns schema + permission checks) + a one-line registration from `__init__.py`. Every new feature, and every *touched* old feature, follows it:
- New logic -> `<feature>_engine.py` (imports only `const.py`, other engines, `homeassistant.util`; **no** `hass` where avoidable).
- New websocket commands -> `<feature>_websocket_api.py` exposing `async_register(hass)`; `__init__.py` gains **one** call line.
- New services -> same module, registered from the same function.
- Dependency direction is strictly `__init__ -> *_websocket_api -> *_engine -> const`. `__init__.py` is never imported by any other module.
- **Extraction #1 (do first, low risk, test-enabling):** lift static-path + dashboard-resource registration (`__init__.py` ~12500-12700, the "four-step pattern per card" repeated ~14 times) into `frontend.py` driven by a table `CARDS = [(url_const, filename, name), ...]`. A guard test asserts every `card/*.js` and `panel/*.js` has a table row. Adding a card becomes one table row instead of four edits across `const.py` and `__init__.py`.
- **Rule:** a *move-only* commit (no behaviour change) lands separately from any behaviour change, and only after a characterization test (ws contract, or snapshot of a handler's response for seeded input) covers the code being moved.
- **Frontend:** new views/cards = new files under `card/`. For the 31k-line calendar card, add new views as separate modules loaded by dynamic `import()` from a new served path; do not append. Keep the duplicated `__fhT/__fhEsc/__fhSweep` helper block byte-identical across files and enforce it with a guard script (diff the block between files in CI) until/unless a shared ES module is introduced deliberately.

**When to use:** Always (PROJECT.md out-of-scope: no big-bang rewrite).
**Trade-offs:** The monoliths shrink only opportunistically; but risk per change stays small and tests accumulate where change happens.

### Pattern 6: Tag-driven release, branch-driven preview

**What:** Preview consumes **branches/SHAs**; Home consumes only **release tags**.
```
feature branch -> deploy-preview feature/x -> she tries it (UAT) -> "yes"
   -> merge to main (fast-forward or merge commit, so the SHA she approved is the SHA released;
      otherwise deploy-preview main once more as the final check)
   -> bump manifest.json version + docs/family/whats-new.md + CHANGELOG
   -> git tag vX.Y.Z (== manifest version)  -> release.yml: CI again, verify tag == manifest.version,
      create GitHub Release (notes = whats-new entry)
   -> Home: HACS shows update (custom repository on the fork) -> developer clicks Update -> restart in a quiet moment
```
**Why HACS-from-release-tag and not folder copy:** HACS offers the 5 latest releases plus the default branch for custom repositories; selecting a release tag gives an auditable, reversible install ("redownload previous release"), and HACS is already how Home installed the integration. Copying a folder works but leaves no record of which version Home runs and invites copying an unsigned-off branch. The integration's own zip self-updater (`updater.py`, no checksum/signature per CONCERNS) must **not** be used as the release path.
**Trade-offs:** Requires disciplined version bumps (HACS needs `manifest.json` `version` and tag to agree). Ship without `zip_release` (the integration lives at `custom_components/family_hub/`, HACS' default layout). Re-point Home's HACS custom repository from `JVarhol/...` to `Future-Bridge-AI/...` once (storage in `.storage` is keyed by domain/entry and is unaffected).

---

## Data Flow

### Deploy flow (code)

```
developer working copy ──(edit)──▶ Dev HA (bind-mount, restart for py / hard-refresh for JS)
        │ git push branch
        ▼
GitHub ── PR ──▶ CI gate (ruff, hassfest, HACS validate, pytest, card smoke, guards)
        │ deploy-preview <ref>
        ▼
Preview host: fetch ref ─▶ rsync --delete ─▶ restart HA ─▶ healthy ─▶ stamp build marker
        │ she opens Preview (Companion app / kiosk bookmark)
        ▼
UAT result ("yes"/"change X") ──▶ GitHub issue (family_request template) / PR comment
        │ yes
        ▼
merge main ─▶ tag vX.Y.Z ─▶ release.yml ─▶ GitHub Release ─▶ Home HACS update ─▶ restart
```

### Seed flow (data)

```
tools/seed/data/*.yaml (relative dates)
        │ tools/seed/cli.py seed --target preview
        ▼
ha_client ──REST──▶ /api/onboarding/*   (fresh volume only)  ─▶ owner + token
          ──REST──▶ /api/config/config_entries/flow           (Local Calendar, Local To-do, family_hub entry)
          ──REST──▶ /api/services/calendar.create_event, todo.add_item
          ──WS────▶ config/auth/*, person/create, lovelace/*
          ──WS────▶ family_hub/* commands + family_hub.* services  (chores, rewards, meals, PINs)
        ▼
HA writes its own .storage/* and family_hub_* Stores (+ family_hub_backups/*)   ← never touched directly
```

### Reset flow

```
reset-preview:  docker compose stop ─▶ rm -rf <preview-config>/{.storage,family_hub_backups,*.db,*.log*,...}
                (keep: configuration.yaml from template, custom_components/ is re-deployed)
                ─▶ start ─▶ onboard ─▶ seed ─▶ stamp
```
**Critical:** wipe `family_hub_backups/` (`SETTINGS_BACKUP_DIR_NAME`) together with `.storage/family_hub_*`. `store.py` auto-restores a backup file whenever primary storage is empty; a half-reset resurrects the old family data. The simplest correct reset is "delete the entire config volume, re-render from `config-template/`".

### Test flow

```
tests/python (CI + local):  engine funcs on dicts ─▶ ws via hass_ws_client ─▶ setup_entry smoke
tests/js     (CI + local):  harness page + mock hass/fetch + fixtures ─▶ card renders ─▶ assertions / screenshots
tests/e2e    (local, vs Preview): real login ─▶ real cards ─▶ screenshots ─▶ docs/family/img (selected)
                      ▲
                      └── fixtures recorded from seeded Dev (Pattern 4)
```

### Key Data Flows

1. **Code to Preview:** git ref -> filesystem copy -> HA restart; no HACS, no network pull by HA itself.
2. **Code to Home:** release tag -> HACS -> filesystem -> HA restart; the only path.
3. **Data to Preview:** seed YAML -> public HA/Family Hub APIs -> HA Stores. One-directional. Preview data never flows to Home; Home data never flows to Preview.
4. **Evidence to her:** Playwright against Preview -> before/after screenshots -> `whats-new.md`.

---

## Test Harness Architecture

| Layer | What it proves | Runs in | Tooling | Notes |
|-------|----------------|---------|---------|-------|
| L0 Static | Syntax, style, repo invariants | CI + pre-commit | `ruff`, `node --check card/*.js`, `scripts/check-guards` | Guards: no `*.js` at package root, no `*.bak*`, no tracked `__pycache__`, helper-block parity across cards, every card has a `frontend.py` row, translations key-parity vs `en.json`, `manifest.version` format |
| L1 Engine unit | Chore/reward/goal/routine/timer rules | CI | plain `pytest`, dicts in/out, `freezegun`-style or injected `now` | Engines import `from .const` / `from . import timer_engine` so the package `__init__` is imported; with the real HA installed (via the HA test plugin) that is fine, only slower on first import. No `hass` fixture needed for pure functions. |
| L2 WS / store | Permissions (`_is_admin`, `_has_permission`), PIN lockout, Store load/save/backup/restore, domain-error -> `send_error` mapping | CI | `hass`, `hass_ws_client`, `MockConfigEntry`, `hass_storage` fixtures | Include migration tests that load frozen `tests/python/fixtures/storage/v<N>/` payloads |
| L3 Setup smoke | `async_setup_entry` loads, all `family_hub/*` ws commands registered (compare to `ws_commands.json`), 8 services registered, every card URL served, unload is clean | CI | same plugin | Highest value-per-line test for the 13k-line `__init__.py`; add *before* any extraction |
| L4 Card smoke | Each of the 12 served card modules + panel loads without throwing, defines its custom element, renders with mocked `hass` | CI | Playwright/Chromium, static harness, `page.clock` frozen | Mock **both** `hass.callWS` and `window.fetch` (cards call HA REST, e.g. `/api/calendars/...`, via an authenticated `fetch`); provide `hass.states`, `hass.user`, `hass.language`, `hass.themes` |
| L5 Visual / E2E | Real HA, real login, real rendering; before/after pictures | local/manual or scheduled; **not** PR-blocking | Playwright vs Dev/Preview, auth via tokens in `localStorage` | Output feeds `docs/family/` |

**Use Playwright for all JS tests, not jsdom + Playwright.** One toolchain covers smoke and screenshots; web components with shadow DOM and CSS custom properties (the theme system) are poorly served by jsdom. Cost: a Chromium download in CI (~1 min with caching).

**Python/HA version coupling (verified):** `pytest-homeassistant-custom-component` latest (0.13.375) pins `homeassistant==2026.10.4` and requires **Python >= 3.14**; HA core's `.python-version` is 3.14.9. CI must therefore use Python 3.14, and the Dev/Preview/Home HA image should be on (or close to) the same HA version as the one the tests run against. Decide a support policy in the foundation phase: "latest HA stable, upgrade Preview first, then Home" — not a matrix of old versions. Also note `hacs.json` claims `homeassistant: 2024.1.0` but `__init__.py` uses `StaticPathConfig` / `async_register_static_paths` (added around HA 2024.7), so the declared minimum is already wrong; raise it to the version actually tested.

---

## CI Architecture

Four workflows, all hosted on GitHub, none needing an HA instance:

| Workflow | Triggers | Jobs | Required to merge? |
|----------|----------|------|--------------------|
| `validate.yml` | push, PR, daily cron, manual | `hassfest` (`home-assistant/actions/hassfest@master`), `hacs/action@main` with `category: integration` | Yes (hassfest/HACS will flag manifest, translations, brand, `hacs.json` issues — expect a first red run on the forked manifest) |
| `ci.yml` | PR, push to main | `lint` (ruff), `guards`, `pytest` (Python 3.14), `card-smoke` (Playwright, cached browsers) | Yes, after each layer is introduced (add jobs incrementally; start required checks small) |
| `release.yml` | tag `v*` | verify tag == `manifest.json` version, re-run ci, create GitHub Release (notes from `docs/family/whats-new.md`) | n/a |
| `deploy-docs.yml` | existing | unchanged; keep path filters on `website/**` | n/a |

Note: running hassfest/HACS validation on a schedule catches upstream HA or HACS rule changes against an otherwise untouched main.

---

## Component Boundaries (what talks to what)

| Component | May call | Must NOT |
|-----------|----------|----------|
| Dev HA | Local files (bind-mount), Dev seed tool | Reach Preview/Home hosts; use real notify targets |
| Preview HA | Its own volume, its own seed tool | Mount Home volumes, share Docker networks with Home, hold Home tokens, have real notify/calendar integrations |
| Home HA | HACS (release tags only) | Receive branch builds, seed data, test fixtures, `tools/`/`dev/`/`tests/` |
| `deploy-preview` | Preview host (SSH), git | Touch Home in any way (no Home hostname/credentials in its config) |
| Seed tool | HA REST/WS of the *named target*, reads `tools/seed/data` | Write `.storage` of a running HA; accept a `--target home` (hard-code the allow-list `dev|preview`; refuse unknown targets and refuse non-LAN-private/non-allow-listed hosts) |
| `tests/python` | In-process HA test fixtures | Any real network or Docker |
| `tests/js` | Static files under `custom_components/family_hub/card|panel`, mocked hass | Real HA |
| `tests/e2e` | Dev/Preview URLs | Home URL |
| Release pipeline | GitHub Releases | Push to Home; Home pulls via HACS |

The `--target` allow-list in the seed tool is the code-level guard behind the "never test on Home" rule.

---

## Anti-Patterns

### Anti-Pattern 1: Preview as "a second user/area on the Home HA"
**What people do:** Create a test dashboard and test calendars inside Home to avoid a second install.
**Why it's wrong:** An integration crash, Store migration or restart still hits the family; real calendars/notify targets are one misconfiguration away.
**Do this instead:** A separate instance on separate volume/port/network; Home never sees branch code.

### Anti-Pattern 2: Seeding by editing `.storage` JSON / committing a config-volume snapshot
**What people do:** Hand-craft or snapshot `.storage` files (auth, onboarding, registries) and commit them.
**Why it's wrong:** `.storage` formats are internal and change with HA releases; auth files contain password hashes and tokens; HA overwrites storage from memory on shutdown, so edits made while running are lost.
**Do this instead:** Public API seeding (Pattern 3). Allow `.storage` fixtures only inside pytest (frozen Store payloads for migration tests) where no live HA is involved.

### Anti-Pattern 3: Absolute dates in seed data
**What people do:** Seed "Tue 3 Nov dentist".
**Why it's wrong:** By next week Preview shows an empty past; she concludes the app is broken/empty.
**Do this instead:** Date offsets + `preview-refresh` (cron or manual) to re-lay the week.

### Anti-Pattern 4: Reset that leaves `family_hub_backups/` behind
**What people do:** Delete `.storage/family_hub_*` only.
**Why it's wrong:** `store.py` restores backups when primary storage is empty -> "reset" resurrects old data.
**Do this instead:** Wipe the whole config volume and re-render from template.

### Anti-Pattern 5: Bind-mounting a mutable git checkout into Preview
**What people do:** Mount the repo clone and `git checkout` branches under a running HA.
**Why it's wrong:** HA has already imported modules; the card hash was computed at startup; half-switched trees produce mixed states, and stale files survive.
**Do this instead:** `rsync --delete` of one exported ref, then restart. Bind-mount only in Dev, where the developer drives restarts.

### Anti-Pattern 6: Hand-built fake `homeassistant` stub for tests
**What people do:** (the upstream author did) maintain a stub package imitating HA.
**Why it's wrong:** Drifts from real HA behaviour; was never committed here, so there is nothing to preserve.
**Do this instead:** `pytest-homeassistant-custom-component` (real HA fixtures), per PROJECT.md decision.

### Anti-Pattern 7: Releasing from a branch or by copying a folder to Home
**What people do:** Point Home's HACS at a branch/main or copy files.
**Why it's wrong:** Home may run something she never saw; no rollback target; no record.
**Do this instead:** Tag only the SHA that passed Preview and CI; Home updates via release.

### Anti-Pattern 8: Extraction by big-bang file split
**What people do:** Split `__init__.py` into 30 modules in one PR.
**Why it's wrong:** No tests -> impossible to verify; import-order and `websocket_api` naming collisions (documented in ARCHITECTURE.md) are easy to trigger.
**Do this instead:** Pattern 5: L3 smoke + ws contract first, then move-only commits, opportunistically.

### Anti-Pattern 9: Making the visual tests PR-blocking too early
**What people do:** Pixel-diff screenshot gates from day one.
**Why it's wrong:** Font/OS rendering differences cause flake; developer starts ignoring red CI.
**Do this instead:** Block PRs on smoke (renders without errors, key text present); keep screenshots as artifacts/evidence until stable.

---

## Growth Considerations

(Adapted: there are two users and one family; what grows is the code and the number of changes she requests.)

| Concern | Now | After ~10 releases | After ~30 releases |
|---------|-----|--------------------|--------------------|
| `__init__.py` size | 13k lines, untested | Frontend registration and 1-2 touched features extracted; smoke + contract tests guard the rest | Net-new features all in modules; `__init__` shrinks only where touched |
| Preview data realism | Hand-written seed | Seed includes edge cases she hit ("a chore on a birthday") | Seed versioned alongside Store schema versions |
| HA upgrades | Manual | Preview-first canary, pinned tags | Optional scheduled CI job against HA `dev`/beta (informational only) |
| Release hygiene | Manual bump | `release.yml` enforces tag == manifest | Changelog generated from `whats-new.md` |

### Scaling Priorities

1. **First bottleneck:** developer time lost to environment friction (restarting, re-seeding). Fix: `dev-reset` fast path, `preview-refresh` instead of full reset.
2. **Second bottleneck:** confidence in changing the monoliths. Fix: smoke + ws contract + characterization tests, accumulating where changes happen.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Home Assistant onboarding API | `GET /api/onboarding`, `POST /api/onboarding/users`, `core_config`, `analytics`, `integration` (steps `user`, `core_config`, `integration`, `analytics`); unauthenticated for `users`, bearer for the rest | Verified in HA source (`components/onboarding/views.py`). Only works while onboarding is incomplete -> the fresh-volume path of reset |
| HA REST + WS | Bearer long-lived token; WS `auth` message then commands | Seeder and E2E runner |
| Local Calendar / Local To-do | Config-flow created entries (UI-only integrations, no YAML) | Seeder drives flows; entity ids depend on names — define names in seed data and assert on the resulting entity ids |
| HACS | Custom repository, release tag | `manifest.json` requires `domain, documentation, issue_tracker, codeowners, name, version`; `brand/icon.png` required; releases optional but preferred (5 latest + default branch offered) |
| GitHub Actions | hassfest, `hacs/action`, own workflows | `hacs/action` inputs: `category`, `ignore` |
| Tailscale (optional v2) | `tailscale serve` on the Preview host, HA `http:` `use_x_forwarded_for` + `trusted_proxies` | Only if remote access is requested |
| Grocy | Disabled in Dev/Preview unless a Dev-only mock is added | Keeps API key out of non-Home envs |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Seed tool <-> Family Hub integration | Public websocket commands / services / config flow only | If a needed command doesn't exist, prefer adding a small admin-gated command or using existing services over writing Store files |
| Test harness <-> cards | Mock `hass` + `fetch`; fixtures recorded from seeded Dev | Mocks must implement exactly the `callWS` types each card issues; record, don't hand-write |
| `frontend.py` <-> `__init__.py` | `await frontend.async_register(hass, entry)` | Replaces ~200 lines of repeated registration |
| `*_websocket_api.py` <-> `__init__.py` | `async_register(hass)` single call | Never import `__init__` from submodules |
| CI <-> release | Same checks re-run on tag | A tag can't ship what main's CI wouldn't pass |

---

## Suggested Build Order (dependencies)

```
0 Foundation hygiene ──┬──────────────────────────────────────────────┐
  (dupes, translations, │                                              │
   pycache, identity,   ├─▶ 1 Cheap CI skeleton ───────────┐           │
   version scheme,      │   (ruff, guards, hassfest, HACS) │           │
   min HA)              │                                  │           │
                        ├─▶ 2 Dev env ─▶ 3 Seed ─▶ 4 Preview ─▶ 5 Her access + family docs
                        │      │          │          │ (deploy/reset)        │
                        │      │          │          └───────▶ 8 Release pipeline ─▶ Home
                        │      │          └─▶ (recorded fixtures) ─▶ 7 JS harness ─▶ 9 Playwright evidence
                        └─▶ 6 pytest: engines ─▶ ws/store ─▶ setup smoke ─▶ ws contract ─▶ 10 Extraction (rolling)
```

| # | Component | Depends on | Why this position |
|---|-----------|------------|-------------------|
| 0 | Foundation hygiene (remove root `.js` dupes + `.bak`, translations parity, untrack pyc, fork identity, version scheme, min HA) | — | Compose mounts and `rsync` deploy ship the folder as-is; dupes/stale translations would ship to Preview. hassfest/HACS validation can't go green before the manifest/identity are fixed. |
| 1 | Cheap CI skeleton: ruff, `node --check`, `check-guards`, hassfest, HACS | 0 | Zero test dependencies, prevents the foundation regressions (dupes reappearing) from day one |
| 2 | Dev environment (`compose` + config template + `dev-up`) | 0 | Needed for everything user-visible; also the place where seed and recorders are developed |
| 3 | Onboarding + seed tool, seed data | 2 | Seeds must exist before Preview is worth showing her; developed against throwaway Dev where failure is free |
| 4 | Preview environment: host provisioning, `compose.preview.yaml`, `deploy-preview`, `reset-preview`, `preview-refresh`, Preview identity/theme | 2, 3 | Reuses the same compose and seed; adds host + deploy + reset. First point where she can see something |
| 5 | Her access (Companion app server, kiosk bookmark) + `docs/family/getting-started.md` | 4 | UAT for the Preview phase is *her* doing it |
| 6 | pytest harness: L1 engines -> L2 ws/store -> L3 setup smoke + `ws_commands.json` | 0 (independent of 2-5) | Can run in parallel with 2-5 (matches PROJECT.md "Phase 3 may overlap Phase 2's tail"). Engines first: cheapest, no HA fixtures |
| 7 | JS harness (Playwright, mocks, fixtures) | 3 (for recorded fixtures), 0 | Fixtures from seeded Dev give realistic data; first version can use a minimal hand-written `hass` and be upgraded |
| 8 | Release pipeline (`release.yml`, version bump process, HACS repo re-point at Home) | 1, 6 (tests green), 4 (sign-off gate exists) | Must exist before the first change is released to Home; first release can be a no-op version to rehearse the path |
| 9 | Playwright E2E screenshots against Preview -> `whats-new` pictures | 4, 7 | Evidence for the family loop; non-blocking |
| 10 | Rolling extraction (`frontend.py` first) | 6 (L3 smoke + contract) | Never extract before the safety net; `frontend.py` is the lowest-risk first move and unblocks "add a card = one row" |

**Parallelism:** 6 can start as soon as 0 is done and proceed alongside 2-5. 1 can land on the same day as 0. 8 can be developed while 5's UAT is in progress.

**Critical path to "she sees something":** 0 -> 2 -> 3 -> 4 -> 5 (aim: this is the first user-visible milestone; do not gate it on tests, CI, or extraction beyond step 1).

---

## Sources

- HA onboarding endpoints and step semantics — `home-assistant/core` `homeassistant/components/onboarding/views.py` (HIGH): https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/onboarding/views.py
- HA authentication / long-lived token via websocket `auth/long_lived_access_token` (HIGH): https://developers.home-assistant.io/docs/auth_api.html and https://home-assistant.io/docs/authentication
- `pytest-homeassistant-custom-component` 0.13.375: requires Python >=3.14, pins `homeassistant==2026.10.4` (HIGH, PyPI JSON): https://pypi.org/pypi/pytest-homeassistant-custom-component/json
- HA core Python version 3.14.9 (HIGH): https://raw.githubusercontent.com/home-assistant/core/dev/.python-version
- HACS integration publishing rules (manifest keys, `brand/icon.png`, releases: 5 latest + default branch) (HIGH): https://hacs.xyz/docs/publish/integration
- HACS GitHub Action workflow and `ignore` checks (HIGH): https://hacs.xyz/docs/publish/action
- `zip_release` / `filename` semantics (MEDIUM, search summary): https://hacs.xyz/docs/publish/start
- hassfest for custom integrations (HIGH): https://github.com/home-assistant/actions and https://developers.home-assistant.io/blog/2020/04/16/hassfest
- Repo evidence (HIGH): `custom_components/family_hub/config_flow.py` (dashboard cannot be created by the integration; 11-step flow), `store.py` + `const.py:174` (`family_hub_backups/` auto-restore on empty storage), `__init__.py:12190-12600` (static path + resource registration; storage-mode only), `hacs.json`, `manifest.json`, `card/*.js` (cards use authenticated `fetch` to HA REST).
- Training-knowledge claims, MEDIUM: Companion app multi-server support; Tailscale `serve` + HA `trusted_proxies` setup; `async_register_static_paths` introduced ~HA 2024.7; Playwright `page.clock`; `syrupy` bundled with the HA test plugin.

---
*Architecture research for: Dev / Family Preview / Home environments, tooling, tests, CI and release flow around the `family_hub` HA integration*
*Researched: 2026-10-26*

## Gaps to Verify in Phase-Level Research

- **Dashboard creation path:** storage-mode dashboard via WS (`lovelace/dashboards/create`) vs YAML-mode dashboard entry in `configuration.yaml` while root lovelace stays in storage mode (needed for the integration's auto resource registration). Spike on a throwaway Dev before committing the seed design.
- **Family Hub admin commands for seeding:** confirm which `family_hub/...` commands can create chores/rewards/goals/routines/PINs/meals and which require kiosk elevation or PIN state; any gap may need a small seeding-only command or direct use of services.
- **Config flow automation:** member -> HA user -> calendar entity mapping step ids and field names (`member_profile` loops per member) must be validated by actually driving the flow.
- **Minimum supported HA version:** confirm exact release that introduced `StaticPathConfig` and set `hacs.json` accordingly.
- **Card mock surface:** the exact set of `hass` properties, `callWS` types and REST paths each card touches (149 `localStorage` uses, authenticated `fetch` calls) — derive from recorded traffic rather than reading 62k lines.
- **Secure-context dependencies:** which card behaviours (calendar card has 3 hits) need HTTPS and whether Home itself is on HTTPS.
- **Preview host:** what hardware actually exists at home (decision input, not research).
- **Python 3.14 locally:** the developer's laptop must run Python 3.14 for the HA test plugin; confirm dev machine/devcontainer provides it (a devcontainer or `uv` pin avoids "works on CI only").
