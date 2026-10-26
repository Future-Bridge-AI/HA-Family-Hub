# Roadmap: Family Hub (Future-Bridge-AI fork)

## Overview

This milestone turns the upstream Family Hub integration into our own fork that is safe to change, with a Family Preview the family product owner can use every day. It runs in four steps. First, clean the repo so edits land in the files Home Assistant actually serves (invisible to the family). Second, stand up Dev and an always-on Family Preview with our pretend family's week, which is the first thing she sees. Third, add a test and CI safety net so changes cannot quietly break Preview. Fourth, run the family-led loop: she asks in her own words, tries the change in Preview, signs off, and only then does Home get a tagged release. Phases 1 and 2 are prerequisites. Phase 3 depends only on Phase 1 and may overlap the tail of Phase 2. From Phase 2 on, every phase ends in something she can try in Preview, and its success criteria are written as things she does and sees.

Note: `v1.0` below is the GSD planning milestone label, not the integration's release version. The fork continues the integration's own numbering above 1.168.85 (see FOUND-07).

## Milestones

- 🚧 **v1.0 Family Preview Loop** - Phases 1-4 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Clean Foundation** - One served copy of every card, panel and translation, no tracked build junk, and our own fork identity, version scheme and pinned HA version
- [ ] **Phase 2: Dev + Family Preview** - One-command Dev plus an always-on, isolated Family Preview with seeded pretend family data, `deploy-preview` / `reset-preview`, and her one-tap non-admin access
- [ ] **Phase 3: Safety Net** - Python engine and setup-smoke tests, card smoke tests, Preview screenshots, and green CI that blocks regressions before they reach Preview
- [ ] **Phase 4: Family-Led Customisation Loop** - She ranks the backlog, asks in her own words, signs off in Preview, and Home receives only tagged, rehearsed, rollback-ready releases

## Phase Details

### Phase 1: Clean Foundation

**Goal:** As a developer, I want to work in a clean fork with one served copy of every file, so that each edit lands where Home Assistant loads it.
**Mode:** mvp
**Depends on:** Nothing (first phase)
**Requirements:** FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, FOUND-07, FOUND-08, FOUND-09
**Success Criteria** (what must be TRUE):
  1. Each card and panel exists only in the served `card/` and `panel/` folders, and each translation only in `translations/`. No root-level duplicate `.js`, `card/family-week-calendar-card.js.bak_divfix`, truncated root `de`/`en`/`es`/`fr.json` or `strings.json` remains. All root-only content was reviewed before deletion and the outcome recorded in `01-TRIAGE.md`; the 9 orphan `de`/`es` keys were reviewed and not ported, because no served code uses them (D-06).
  2. Italian, Dutch, Polish, Portuguese and Brazilian Portuguese sit in `translations/` next to `de`/`en`/`es`/`fr`, each with the same 2,139 keys as `translations/en.json`, so HA can load all nine languages the README advertises. The `fh_ui` category is preserved.
  3. A fresh clone tracks no `.pyc` files and has no `\Screenshots/` folder, no duplicate icon or logo files and no empty `custom_components/family_hub/readme.md`. `.gitignore` covers `.env`, `*.bak*`, `family_hub_backups/` and `.storage/`.
  4. `manifest.json` links, codeowners, README badges, HACS links and the docs site all point at `Future-Bridge-AI/HA-Family-Hub`, with upstream credit and GPLv3 intact. `manifest.json` carries the next fork version under the recorded version scheme. `domain`, service names, websocket prefixes and card tags are unchanged.
  5. One pinned HA version is recorded for Dev, Preview and tests. The minimum HA version in `hacs.json` matches what the code actually needs. The failure list from the first hassfest and HACS validation run is written down for the Safety Net phase.

**Plans:** 2/7 plans executed

Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Untrack bytecode, write the triage record, remove junk files, extend .gitignore (wave 1)
- [x] 01-03-PLAN.md — Fork identity in manifest, README and the docs site, plus the non-blocking validate.yml workflow (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 01-02-PLAN.md — One served copy of each card and panel: port any root-only hunk the triage marks "ported hunk" (own commit), then delete the 14 root card/panel duplicates (wave 2)
- [ ] 01-04-PLAN.md — versions.env pin 2026.10.4, hacs.json minimum 2024.12.0, D-19 version checkpoint, then manifest 1.169.0 (wave 2, has checkpoint)
- [ ] 01-06-PLAN.md — Move it/nl/pl/pt/pt-BR into translations/ unchanged (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 01-07-PLAN.md — Delete the truncated root translations and strings.json, then the .bak_divfix backup (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*
- [ ] 01-05-PLAN.md — Validation baseline: local hassfest, HACS prediction, Phase 1 sweep, the developer's hosted run recorded (wave 4, runs last, has checkpoint)

**UI hint**: no
**Research:** Not needed. The hassfest/HACS validation spike inside this phase is the research.

### Phase 2: Dev + Family Preview

**Goal:** As a family product owner, I want to use a safe Family Preview of our week on my phone, so that I can try changes without risking Home.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** DEV-01, DEV-02, DEV-03, PREV-01, PREV-02, PREV-03, PREV-04, PREV-05, PREV-06, PREV-07, PREV-08, ACCESS-01, ACCESS-02, ACCESS-03, ACCESS-04, ACCESS-05
**Success Criteria** (what must be TRUE):
  1. She can open Family Preview at any time, in one tap from her phone (or from a bookmarked tablet), at its own stable home-network address. She signs in with her own non-admin account and sees only the Family Hub dashboard. It is clearly labelled PREVIEW, with its own name and theme, so she never mistakes it for Home.
  2. Whenever she opens Preview, it shows a realistic current week for our pretend family: members, calendars, events, meals, chores, rewards and to-do lists. Nothing she does there sends a reminder, alert, Daily Digest, nudge or timer alarm to a real phone or speaker, or touches the real family calendars and lists.
  3. Using only the plain-language Getting started guide in `docs/family/`, she opens Preview on her own, finds today's plan, ticks a chore and redeems a reward.
  4. The developer checks a trivial visible change (e.g. a title text) in Dev, which starts with one command on the same pretend data and shows edits live. The developer then runs `deploy-preview <branch>`. After a refresh, she sees the new text and a newer build stamp in Preview and confirms it.
  5. After she has ticked chores and redeemed rewards, one `reset-preview` brings back the original pretend week with no old data resurrected. On a fresh Preview the Family Hub dashboard and cards are in place without manual setup, and Dev resets the same way.

**Plans:** TBD
**UI hint**: yes
**Research:** NEEDS research-phase before planning (`/gsd-plan-phase --research-phase 2`). Open questions from research/SUMMARY.md:
- Dashboard and resource creation path: storage-mode `lovelace/dashboards/create` or a YAML-mode dashboard.
- Which `family_hub/*` commands can seed chores, rewards, goals, routines, meals and PINs without a kiosk session.
- Driving the 11-step config flow, including the `member_profile` loops.
- Setting up her non-admin dashboard and sidebar reproducibly.
- HTTPS secure-context differences.
- Preview host hardware and the Companion second-server setup.

**Decisions due:**
- Where Preview runs: an always-on Docker host, not the laptop.
- Preview is a separate instance from Home.
- How she reaches it: LAN-only (Tailscale deferred).

### Phase 3: Safety Net

**Goal:** As a family product owner, I want to trust that no change can quietly break my Preview, so that trying new things always feels safe.
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, CI-01, CI-02, CI-03, CI-04
**Success Criteria** (what must be TRUE):
  1. She receives an automatically captured set of Preview screenshots (calendar, today, chores, rewards, to-dos and the other screens she uses) and recognises each one. The same capture can be re-run to give her before/after pictures of any change.
  2. After the safety-net changes (lint fixes included) are deployed to Preview, she walks her usual routine (find today's plan, tick a chore, redeem a reward) and everything works exactly as before.
  3. The developer runs the Python tests with one command on the pinned HA and Python versions. The chore, reward, goal, routine and timer engines are covered for their main behaviours, including week, month and DST boundaries.
  4. Every push and PR on GitHub runs ruff, the Python tests, the JS checks, the card smoke tests, and HACS and hassfest validation, and all of them are green.
  5. CI fails, before the change can reach Preview, on any change that:
     - drops a registered `family_hub/...` websocket command or one of the 8 services
     - stops a served card or panel from loading and rendering with a mocked `hass`
     - re-adds a stray `.js` outside `card/`/`panel/`, a tracked `.pyc` or a `*.bak*` file
     - lets translation keys drift from `translations/en.json`

**Plans:** TBD
**UI hint**: no
**Overlap:** May start before the tail of Phase 2 is finished. Engine tests, lint and CI need only Phase 1. The screenshot work (TEST-05) needs Preview running with its seed data.
**Research:** Targeted.
- Needs research: the hassfest/HACS failure list recorded in Phase 1 and the `fh_ui` category exception decision.
- Needs research: the per-card `hass`/`callWS` mock surface.
- Needs research: the two modules that did not register in the jsdom spike (`card/family-hub-my-chores-card.js`, `panel/theme-builder-panel.js`).
- Standard (no research): the engine tests and the CI skeleton.

### Phase 4: Family-Led Customisation Loop

**Goal:** As a family product owner, I want to ask for changes in my own words and sign them off in Preview, so that only what I approve reaches Home.
**Mode:** mvp
**Depends on:** Phase 2, Phase 3
**Requirements:** LOOP-01, LOOP-02, LOOP-03, LOOP-04, LOOP-05, REL-01, REL-02, REL-03, REL-04
**Success Criteria** (what must be TRUE):
  1. She has seen the candidate backlog and put it in her own priority order. It includes editing an existing calendar event, Month-view meal drag-to-reorder, finishing the Theme Builder, and anything from her first week. She then asks for a change in her own words (in person, or via the Family request template with no GitHub account needed) and agrees "I do X, I see Y" checks for it before building starts.
  2. She tries that change in Preview, checking the build stamp, and her answer (works / doesn't work / works but confusing) is recorded as the verification. Nothing reaches Home until she says yes.
  3. After her sign-off, the family's real Home updates to a tagged release whose tag matches the version in `manifest.json`, with all the real calendars and lists still there. Before that first release, Home was switched once from the upstream repo to our fork, after a full HA backup.
  4. For that release she can read a short, jargon-free `docs/family/whats-new.md` entry with a screenshot, saying what changed and where to find it.
  5. A rollback following `docs/RELEASING.md` has been rehearsed on Preview, and she saw the earlier build stamp come back. Any code moved out of `__init__.py` or the calendar card (starting with card and resource registration) lands only behind the safety-net tests and leaves everything she uses in Preview working as before.

**Plans:** TBD
**UI hint**: no
**First loop change:** Use a small request she picks so it fits this phase. Bigger backlog items she promotes (FEAT-01..06 in REQUIREMENTS.md v2) become their own phases via `/gsd-phase`, each with its own UI design step.
**Research:** Targeted.
- Standard: the release and HACS update mechanics.
- Needs research: the one-time HACS repository switch on Home.
- Needs research, once ranked: whichever backlog item she ranks first. Edit-event needs calendar card internals, Local Calendar editability and recurrence.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4. Phase 3 depends only on Phase 1, so it may begin during the tail of Phase 2. Phase 4 waits for both.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Clean Foundation | 2/7 | In Progress | - |
| 2. Dev + Family Preview | 0/TBD | Not started | - |
| 3. Safety Net | 0/TBD | Not started | - |
| 4. Family-Led Customisation Loop | 0/TBD | Not started | - |

---
*Roadmap created: 2026-10-26. Coverage: 43/43 v1 requirements mapped.*
