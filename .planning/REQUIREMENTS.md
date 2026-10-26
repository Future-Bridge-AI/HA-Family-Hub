# Requirements: Family Hub (Future-Bridge-AI fork)

**Defined:** 2026-10-26
**Core Value:** The family product owner can use a working Family Hub every day and see each change she asks for appear in a safe Preview before it reaches the family's real Home setup — without anything breaking the real calendars and lists.

Sources: `docs/onboarding-findings.md`, `.planning/PROJECT.md`, `.planning/research/SUMMARY.md`, `.planning/codebase/`.
"She" / "her" below means the family product owner (non-technical, the real user). "Developer" means the repo owner.

## v1 Requirements

Requirements for milestone 1. Each maps to one roadmap phase.

### Foundation (clean, safe-to-edit repo)

- [ ] **FOUND-01**: Developer can edit a card or panel and the change can only land in the served copy — root-level duplicate `.js` files and `card/family-week-calendar-card.js.bak_divfix` are removed after a per-file diff review, and any root-only content worth keeping is ported into `card/` or `panel/` first
- [ ] **FOUND-02**: Users with Italian, Dutch, Polish, Portuguese or Brazilian Portuguese selected see Family Hub in their language — `it`, `nl`, `pl`, `pt`, `pt-BR` live in `translations/` and are loaded by HA (key parity with `translations/en.json` already verified: 2,139 keys each)
- [ ] **FOUND-03**: Translation files exist in exactly one place — the truncated root `de`/`en`/`es`/`fr.json` are removed after the 9 root-only keys in `de`/`es` are reviewed and ported if wanted, and the unused `strings.json` is removed; the `fh_ui` category is preserved
- [x] **FOUND-04**: The repository tracks no compiled Python (`__pycache__/*.pyc` untracked) and `.gitignore` covers `.env`, `*.bak*`, `family_hub_backups/` and HA `.storage/`
- [x] **FOUND-05**: Repo hygiene is clean — `\Screenshots/` renamed or removed (references updated), duplicate icon/logo files removed after checksum compare, empty `custom_components/family_hub/readme.md` removed
- [ ] **FOUND-06**: The fork has its own identity — `manifest.json` documentation, issue tracker and codeowners, README badges/links, HACS links and the docs site config point at `Future-Bridge-AI/HA-Family-Hub`, with upstream credit and GPLv3 kept; `domain`, service names, websocket prefixes and card tags are unchanged
- [ ] **FOUND-07**: Fork versioning scheme is decided and recorded (continue strictly above 1.168.85, e.g. 1.169.0) and the next version is set in `manifest.json`
- [ ] **FOUND-08**: The declared minimum HA version in `hacs.json` matches what the code actually needs and what is tested, and a single pinned HA version is recorded for Dev, Preview and tests
- [ ] **FOUND-09**: The first hassfest and HACS validation failures are known — validation has been run once and the failure list recorded for the safety-net work

### Dev environment

- [ ] **DEV-01**: Developer can start a Dev Home Assistant with one command (Docker Compose, pinned HA image, port distinct from Home and Preview) with the integration mounted live from the working copy
- [ ] **DEV-02**: Developer sees Python changes after an HA restart and card JS changes after a browser refresh in Dev, without copying files
- [ ] **DEV-03**: Dev starts with realistic demo data from the same seed tool as Preview, and can be reset to a known state (including clearing `family_hub_backups/`)

### Family Preview environment

- [ ] **PREV-01**: She can reach an always-on Family Preview at a stable address on the home network, running as a separate HA instance that shares nothing with the Home setup (own config, own identity, bridge networking, discovery disabled)
- [ ] **PREV-02**: She can tell at a glance she is in Preview, not the real app — distinct name, theme and server entry
- [ ] **PREV-03**: Nothing done in Preview reaches the real world — no reminders, alerts, Daily Digest, nudges or timer alarms are delivered to real phones or speakers, and Preview never connects to the real family calendars or lists
- [ ] **PREV-04**: When she opens Preview she sees a realistic current week — our family members, calendars, events, meals, chores, rewards and the to-do lists the integration needs — generated relative to today so it never goes stale
- [ ] **PREV-05**: Developer can put any branch onto Preview with one command (`deploy-preview <branch>`), which restarts Preview and verifies the new cards are actually being served
- [ ] **PREV-06**: Developer can return Preview to the known seeded state with one command (`reset-preview`), which also clears the integration's own backups so old data cannot come back
- [ ] **PREV-07**: She can see which build she is looking at (a visible version/build stamp) so "did it update?" is never a guess
- [ ] **PREV-08**: The Family Hub dashboard and card resources are created and verified automatically on a fresh Preview — no manual dashboard setup

### Her access and family docs

- [ ] **ACCESS-01**: She signs in to Preview with her own non-admin account and sees only the Family Hub dashboard (other dashboards and admin sidebar items hidden), verified by logging in as her on the real device
- [ ] **ACCESS-02**: She can open Preview in one tap from her phone (HA Companion app second server or home-screen shortcut) and/or a bookmarked tablet dashboard, so it feels like an app
- [ ] **ACCESS-03**: She can read a plain-language "Getting started" guide in `docs/family/` with screenshots from Preview: what each screen is for and how to ask for a change
- [ ] **ACCESS-04**: She can, on her own, open Preview, find today's plan, tick a chore and redeem a reward
- [ ] **ACCESS-05**: She confirms she can see one trivial visible change (e.g. a title text) that the developer deployed to Preview

### Safety net (tests and CI)

- [ ] **TEST-01**: Developer can run a Python test suite locally with one command on the pinned HA/Python versions (`pytest` + `pytest-homeassistant-custom-component`, Python 3.14 via `uv`)
- [ ] **TEST-02**: The pure engines (chore, reward, goal, routine, timer) have unit tests covering their main behaviours, including week/month and DST boundaries
- [ ] **TEST-03**: A setup smoke test loads the integration, checks the registered `family_hub/...` websocket commands against a checked-in contract, checks the 8 services and served card URLs, and unloads cleanly — so a refactor cannot silently drop a command
- [ ] **TEST-04**: Every served card and panel module loads and renders with a mocked `hass` in a JS smoke test
- [ ] **TEST-05**: Developer can capture screenshots of Preview automatically (Playwright), usable as before/after pictures for her
- [ ] **CI-01**: Every push and PR runs Python lint (ruff, narrow rule set) and the Python tests on GitHub Actions
- [ ] **CI-02**: Every push and PR runs JS checks (ESLint narrow set / syntax) and the card smoke tests
- [ ] **CI-03**: Every push and PR runs HACS and hassfest validation, green
- [ ] **CI-04**: CI guards reject regressions of the foundation cleanup — stray `.js` outside `card/`/`panel/`, tracked `.pyc` or `*.bak*`, translation key-parity drift against `translations/en.json`

### Family-led customisation loop

- [ ] **LOOP-01**: She can ask for a change in plain language — in person or via the Family request issue template — without needing a GitHub account; the developer records it in her words
- [ ] **LOOP-02**: Every change has acceptance criteria written as things she will do and see in the app ("I do X, I see Y"), agreed with her before building
- [ ] **LOOP-03**: She tries each change in Preview and her answer (works / doesn't work / works but confusing) is recorded as the verification; nothing goes to Home without her sign-off
- [ ] **LOOP-04**: She can read a short, jargon-free `docs/family/whats-new.md` entry (what changed, where to find it, a screenshot) for every release to Home
- [ ] **LOOP-05**: She has seen the candidate backlog (edit existing calendar events, Month-view meal drag-to-reorder, finishing the Theme Builder, anything from her first week) and decided its priority
- [ ] **REL-01**: Home only ever receives tagged releases — a release workflow checks the tag equals `manifest.json`'s version, re-runs CI and publishes a GitHub Release
- [ ] **REL-02**: Home's HACS is switched from the upstream repo to the fork, once, after a full HA backup
- [ ] **REL-03**: A documented release and rollback procedure (`docs/RELEASING.md`: HA backup first, release at a quiet time, how to roll back) exists and rollback has been rehearsed on Preview
- [ ] **REL-04**: New work that touches `__init__.py` or the calendar card extracts focused modules (strangler pattern, starting with table-driven card/resource registration) only behind the safety-net tests, rather than growing the monoliths

## v2 Requirements

Deferred. Tracked but not in the current roadmap — she decides what gets promoted.

### Features (her call)

- **FEAT-01**: User can edit an existing calendar event's own title, date/time and location (only delete is supported today) — likely top gap
- **FEAT-02**: User can drag to reorder meals in Month view (Week view Edit mode already supports it)
- **FEAT-03**: Theme Builder panel finished and documented
- **FEAT-04**: In-app "What's new" card
- **FEAT-05**: School calendar import via ICS (HA Remote Calendar)
- **FEAT-06**: Photo screensaver (check what the existing screensaver supports first)

### Environments

- **ENVX-01**: Preview reachable from outside the home (Tailscale)
- **ENVX-02**: Wall-tablet kiosk trial of Preview (e.g. Fully Kiosk)
- **ENVX-03**: Multiple seed scenarios (busy week, quiet week, holidays)

### Hardening (from `.planning/codebase/CONCERNS.md`)

- **HARD-01**: Grocy API key and URL handled safely (HTTPS, timeouts)
- **HARD-02**: Consistent escaping for the ~390 `innerHTML` uses
- **HARD-03**: Narrow the ~145 broad `except Exception` clauses
- **HARD-04**: Full `ruff format` / broad lint rule set adopted

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cloud services / hosted backend | Everything stays local on Home Assistant (upstream design, family privacy) |
| Testing changes on the real Home setup | All experiments go to Dev or Preview; Home only gets signed-off releases |
| Real family calendars or data in Preview | Seeded pretend data only, so trying things can't break anything |
| Admin account for her | Non-admin keeps Preview simple and safe |
| Using the built-in self-updater on Home | No checksum/signature check and it bypasses the sign-off gate |
| Auto-deploy / auto-promote to Home | Her sign-off is a manual gate by design |
| Per-branch preview environments | One Preview is enough for one family; avoids confusion |
| Custom in-app feedback form with a backend | Plain-language requests + issue template cover it |
| Forcing her to use GitHub | She is non-technical; the developer transcribes |
| Auto-generated changelogs as "what's new" | She needs jargon-free notes |
| AI paper-schedule scanning / subscriptions / chat features | Cloud-dependent or off-mission |
| Big-bang rewrite of `__init__.py` or the calendar card | Extract incrementally behind tests instead |
| Default HACS store listing | Custom repository is sufficient |
| Relicensing | Derivative work stays GPLv3 |
| Renaming `domain`, services, websocket prefixes or card tags | Would orphan saved dashboards and automations |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Pending |
| FOUND-03 | Phase 1 | Pending |
| FOUND-04 | Phase 1 | Complete |
| FOUND-05 | Phase 1 | Complete |
| FOUND-06 | Phase 1 | Pending |
| FOUND-07 | Phase 1 | Pending |
| FOUND-08 | Phase 1 | Pending |
| FOUND-09 | Phase 1 | Pending |
| DEV-01 | Phase 2 | Pending |
| DEV-02 | Phase 2 | Pending |
| DEV-03 | Phase 2 | Pending |
| PREV-01 | Phase 2 | Pending |
| PREV-02 | Phase 2 | Pending |
| PREV-03 | Phase 2 | Pending |
| PREV-04 | Phase 2 | Pending |
| PREV-05 | Phase 2 | Pending |
| PREV-06 | Phase 2 | Pending |
| PREV-07 | Phase 2 | Pending |
| PREV-08 | Phase 2 | Pending |
| ACCESS-01 | Phase 2 | Pending |
| ACCESS-02 | Phase 2 | Pending |
| ACCESS-03 | Phase 2 | Pending |
| ACCESS-04 | Phase 2 | Pending |
| ACCESS-05 | Phase 2 | Pending |
| TEST-01 | Phase 3 | Pending |
| TEST-02 | Phase 3 | Pending |
| TEST-03 | Phase 3 | Pending |
| TEST-04 | Phase 3 | Pending |
| TEST-05 | Phase 3 | Pending |
| CI-01 | Phase 3 | Pending |
| CI-02 | Phase 3 | Pending |
| CI-03 | Phase 3 | Pending |
| CI-04 | Phase 3 | Pending |
| LOOP-01 | Phase 4 | Pending |
| LOOP-02 | Phase 4 | Pending |
| LOOP-03 | Phase 4 | Pending |
| LOOP-04 | Phase 4 | Pending |
| LOOP-05 | Phase 4 | Pending |
| REL-01 | Phase 4 | Pending |
| REL-02 | Phase 4 | Pending |
| REL-03 | Phase 4 | Pending |
| REL-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0
- Per phase: Phase 1 = 9 (FOUND), Phase 2 = 16 (DEV, PREV, ACCESS), Phase 3 = 9 (TEST, CI), Phase 4 = 9 (LOOP, REL)

---
*Requirements defined: 2026-10-26*
*Last updated: 2026-10-26 after roadmap creation (traceability mapped)*
