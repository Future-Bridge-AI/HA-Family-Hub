# Feature Research

**Domain:** Home Assistant family-hub dashboard (fork of `family_hub`) plus a family-facing Preview / feedback / release workflow for a non-technical product owner
**Researched:** 2026-10-26
**Confidence:** MEDIUM overall. Commercial product claims (Skylight, Hearth, DAKboard) come from vendor-authored or affiliate pages, so they are LOW-MEDIUM. HA platform behaviour (Companion app, non-admin users, kiosk) is MEDIUM, from official docs and community threads plus established HA knowledge. Workflow recommendations (UAT, release notes) are MEDIUM and mostly general practice, adapted to a two-person household.

**Scope note:** Everything under PROJECT.md "Validated" (calendar views, chores/stars/rewards, goals, routines, to-dos, recipes/pantry, timers, screensaver, kiosk PIN, child accounts, reminders, 10 themes, i18n) is out of scope here. Those capabilities already cover most of what Skylight, Hearth and DAKboard sell. This file covers (A) the Preview/feedback/release workflow and (B) the few market-context gaps relevant to the candidate backlog.

---

## Feature Landscape

### A. Family Preview Environment

#### Table Stakes (she will stop using it, or stop trusting it, without these)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| One-tap access: Companion app and/or home-screen icon opening straight to the Family Hub dashboard | A non-technical person judges it by "does it feel like an app". Any URL typing or login friction ends the trial. | LOW | HA Companion app supports multiple servers (iOS 2021.12+, Android 2023.3+), so Preview can be a second server beside Home. Alternative: browser "Add to Home screen" shortcut or PWA, which avoids sharing phone sensors with Preview. Pick one and test on her actual phone. (MEDIUM) |
| Unmistakable "this is PREVIEW, not Home" signal | Two lookalike family apps are the biggest confusion risk. Ticking a chore in the wrong one means silent loss of trust or real-data mistakes. | LOW | Distinct theme or accent colour, instance name "Family Hub PREVIEW", and a banner or title on the dashboard. Reuse the existing theme system rather than new code. Companion app server list also shows the names. |
| Always-on at a stable address | If Preview is down when she gets a free evening, the loop stalls. | MEDIUM | Already a PROJECT.md decision (home machine, Docker Compose). Add a restart policy and a "Preview is up" check. Reachable on home Wi-Fi at minimum. Remote access (Tailscale or Nabu Casa) is an open decision. |
| Non-admin HA user for her with a dashboard that shows only Family Hub | A non-admin user cannot reach Settings or Developer Tools, but HA does not hide dashboard tabs or the sidebar from them. Community reports confirm a restricted user still sees all the other dashboard views. | MEDIUM | Needs a dedicated dashboard, "require admin" on the others, the sidebar hidden per user (profile setting), and optionally kiosk-mode (HACS frontend plugin, per-dashboard or `user_settings`). Many kiosk-mode forks are stale, so verify on the HA version in use. Test by logging in as her. (MEDIUM) |
| Realistic seeded data that is relative to today | "Today's plan" must never be empty or full of last month's events. Stale demo data is the top reason a preview looks broken. | MEDIUM | The seed script must generate events, meals, chores and rewards as offsets from `now`, not fixed dates. Re-run on reset and, ideally, on a nightly schedule. Include several people with colours, a kid with stars near a reward, an overdue chore, a meal on the plan and a recurring event. |
| One-command reset to the known seed state | She will experiment and break things. She must be able to recover without a developer. | MEDIUM | `reset-preview` wipes Local Calendar, Local To-do and `family_hub` stores, then re-seeds. A friendly "reset" the developer can trigger fast. Not a button for her at first. |
| Preview cannot reach the real world (no real notifications, TTS or speakers, no real calendars) | The integration has reminders, Daily Digest, nudges, alarms on speakers and phones. A Preview timer ringing the real kitchen speaker or pushing to the family's phones is a trust-killer. | MEDIUM | Point the `notify.*` target at a null or test-only target in Preview. Do not install the Companion app notify service for the family. Verify poller output goes nowhere real. Test by triggering a reminder in Preview and confirming nobody else is pinged. |
| Deploy from a chosen branch in one command, then tell her what changed | The loop only works if "I changed it" means "it is live in Preview within minutes". | MEDIUM | `deploy-preview <branch>` already planned. Include a post-deploy message template: "what changed, where to tap, what to try". |
| Card cache refresh handled for her | Card JS is content-hash cache-busted already, but the Companion app can still show a stale dashboard. "It looks the same as before" is the classic false UAT failure. | LOW | Document a "pull to refresh / reload app" step in the Getting started guide. Confirm the version shown on screen (see Differentiators). |

#### Differentiators (go beyond the minimum, help the loop feel professional)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Visible version / "last updated" stamp inside Preview (and Home) | She can say "I'm on build 12" when reporting. Removes the "did it refresh?" doubt. | LOW | Show manifest version or deploy timestamp in the More menu or a small footer. Version scheme decision is still pending. |
| Tablet kiosk dashboard for the wall tablet using Fully Kiosk or Companion in locked mode | The real product is a wall tablet. Letting her try the wall experience (screensaver, Privacy mode, wake-on-motion) in Preview is more realistic than phone only. | MEDIUM | Fully Kiosk is the common tool: full screen, hides bars, motion wake. Remote control from HA needs the paid Fully Plus licence (about 8 EUR per device, per the HA community; unverified for 2026). The free Companion app only offers Android screen pinning. Not required for the phone-first trial. |
| "Try this" guided tour per release (3-5 steps with screenshots) | Turns UAT into a 5-minute task she can do on the sofa. | LOW | Same content as acceptance criteria, rendered friendly. Lives in `docs/family/` next to what's new. |
| Before/after screenshots auto-generated from Playwright | Shows the change without her having to open the app. Cheap proof for sign-off. | MEDIUM | Already in the planned safety net. Reuse the same seed data so pictures match what she sees. |
| Seed "scenarios" (a normal Tuesday, a busy Saturday, an empty week) | Lets the developer demo a change on the data where it matters. | MEDIUM | Defer until the base seed works. |

#### Anti-Features (do not build)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Clone real family data into Preview for "realism" | Preview would feel real. | Breaks the Safety constraint, copies private data, and risks real notifications. Out of Scope in PROJECT.md. | Rich pretend data seeded by script; ask her to name 2-3 realistic things to add (a standing activity, a favourite meal). |
| Giving her an admin account "so she can see everything" | Easier for the developer. | Lets her break Preview in ways she cannot fix and exposes confusing developer UI. | Non-admin user plus developer-side reset. |
| Per-branch automatic preview environments (one HA instance per PR) | Common web-dev pattern (Vercel and similar). | Heavy for HA (stateful, volume per branch, ports), and she only needs one Preview. | Single Preview instance; `deploy-preview <branch>` swaps what it runs. |
| Auto-sync Preview from Home or two-way sync | Keeps data fresh. | Same risks as cloning. Creates a path for Preview to write to Home. | One-way: nothing flows from Home to Preview. |
| Making her use the HA UI or HACS to update Preview | "Self-service". | Update flow is a developer tool; she should never see it. | Developer runs `deploy-preview`. |
| Cloud-hosted Preview | Reachable anywhere. | Contradicts local-only design. | Tailscale or Nabu Casa remote access to the local box if remote reach is needed (decision pending). |

---

### B. Family-Led Change-Request, UAT and Release Loop

#### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Plain-language request intake | She must be able to ask in her own words. A form full of fields means she stops asking. | LOW | `.github/ISSUE_TEMPLATE/family_request.md` already exists (what were you trying to do / what gets in the way / what would make it better / importance / screenshot). Keep it. Important: GitHub account for her is optional. The developer can file the issue from what she says in person or in a message, with her original words quoted verbatim. |
| Acceptance criteria written as "I do X, I see Y" | General UAT guidance says scripts should follow a real user journey and be written in the stakeholder's language (Given/When/Then is the common pattern, but she needs the plain "I do / I see" form, not the jargon). | LOW | Template block in the issue or a `docs/family/uat/` file: "Open the calendar. Tap Thursday. I see school pickup with Dad's colour." Developer writes, she confirms the wording is right before building. |
| UAT by her, recorded as pass / not yet / confusing | Sign-off needs a clear outcome per criterion. | LOW | Three answers per step (works / does not work / works but confusing). "Confusing" is a valid failure for this audience. Small numbers of steps per round, journeys rather than clicks. |
| Explicit sign-off gate before anything reaches Home | Core Value. Release without her yes is a process failure. | LOW | A checklist in the PR or release issue: "She tried it in Preview on [date]: yes / changes needed". Release tag is created only after the box is ticked. Document it as a rule rather than building tooling. |
| Release to Home from a tagged version, not a branch | Home must receive exactly what she approved. Moving branches break that guarantee. | MEDIUM | HACS custom repositories can install a specific release or tag. Preview runs the branch; Home pins a tag. Fork versioning decision is pending (continue 1.168.x or own scheme). (MEDIUM) |
| Safety net on release: HA backup first and a documented rollback | Wall tablet, timers and calendars are daily-use. A bad release needs a one-step undo. | MEDIUM | Take an HA backup (full or partial) before updating Home. Rollback is installing the previous tag and restoring. The integration's own 12-hourly store backups help but are not a substitute. Release at a quiet time because restarting HA interrupts timers and the wall tablet. |
| "Getting started" guide in plain language | She needs to know what each screen is for before she can judge changes. | LOW | `docs/family/getting-started.md`. Screenshots from the seeded Preview, task-oriented ("find today's plan", "tick a chore", "redeem a reward"), no HA jargon. Keep screenshots regenerable. |
| "What's new" entry per release to Home | Family members need to know something changed and where. | LOW | One entry per release. General release-note guidance agrees on: plain language, lead with the benefit, say where to find it, scannable in about 30 seconds, no developer terms like "deprecation" or "staging". |

#### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Her own priority ranking on the backlog ("nice / easier week / bugging me daily") | Her answers decide order, not the developer's taste. | LOW | The request template already captures importance. Add a GitHub label per level and a simple board view. |
| Show-and-tell loop cadence (weekly 15-minute review at the kitchen table) | Fast feedback, turns UAT into something pleasant rather than homework. | LOW | Process, not code. |
| "What's new" shown inside the app (a small one-time card or More-menu entry) | Whole family sees changes without opening a doc. | MEDIUM | Needs a small card or panel plus a stored "seen" flag. Do after the docs-only version proves its worth. |
| Request-a-change shortcut from within the hub (a More-menu link to the form or a mailto/message) | Lowers the barrier to asking. | LOW | A plain link is enough. Do not build a custom in-app form (see Anti-Features). |
| Release checklist artifact (`docs/RELEASING.md`) that the developer follows every time | Repeatable, safe, low-stress. | LOW | Backup, tag, update Home via HACS, restart at quiet time, verify, write what's new, tell family. |
| Rollback rehearsal in Preview once | Confidence that undo works before it is needed. | LOW | One-time exercise. |

#### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Forcing her to have and use a GitHub account | "Single source of truth". | Non-technical user friction ends feedback. | Developer transcribes; issue links back to her words. |
| Custom in-app feedback form with its own backend | Feels integrated. | Adds storage, auth and moderation for a household of two. Contradicts the local-only, no extra services stance. | Plain link to the request form, or a message to the developer. |
| Auto-promote from Preview to Home on merge, or CI deploying straight to Home | Fast. | Bypasses the sign-off gate that defines the project. | Manual, checklist-driven release after her yes. |
| Using the integration's built-in self-updater on Home | One-click updates. | Upstream self-updater has no checksum or signature check (CONCERNS.md), and it bypasses the sign-off gate. | HACS tagged release, developer-driven. |
| Auto-generated changelogs from commit messages as "what's new" | Zero effort. | Produces developer jargon the audience will not read. | Hand-written entry per release, 3-5 lines plus a screenshot. |
| Heavy formal UAT (test-case spreadsheets, defect severity matrices, exit reports) | Standard enterprise UAT practice. | Overkill and off-putting for a family. | Short "I do / I see" steps and three-answer outcomes. |
| Translating every "what's new" into all supported languages | i18n exists. | Family speaks one language; multiplies effort. | English (or the family's language) only. |

---

### C. Family-Hub / Wall-Tablet Feature Landscape (context for the candidate backlog)

Competitors: Skylight (calendar, chore chart, lists free; Plus subscription adds meal planner, photo screensaver, SideKick paper-to-event AI, Magic Import), Hearth (kid routines, chore chart, per-person profiles, calendar sync, membership-gated), DAKboard/TouchHub (software for your own screen, HA integration, child lock, chores manager on paid plans, photos), plus HA community boards (for example LX Family). Sources are vendor and affiliate content, so treat as indicative.

#### Table Stakes in the category (what buyers assume)

| Feature | Status in this fork | Notes |
|---------|--------------------|-------|
| Shared colour-coded per-person calendar, multiple views | Validated (Week / Month / Planner / Agenda) | |
| Chore chart per kid with tick-off | Validated | |
| Rewards or points | Validated (stars, rewards) | Skylight gates rewards behind a paid extra, so this fork is ahead here. |
| Shared lists (grocery, to-do) | Validated (`todo.*`) | |
| Meal plan | Validated | |
| Glanceable always-on display with screensaver | Validated | |
| Kid-safe interaction (cannot change others' items) | Validated (PIN, child accounts, permissions) | |
| Edit an existing event (time, place, title) | GAP: DOCUMENTATION.md says only delete is supported, and the info popup cannot change summary, time or location | Likely the most visible gap for daily use. Competitors all let you edit. Do not assume; ask her in Preview week one, but expect it to rank above both named backlog items. Complexity MEDIUM (touches the calendar card monolith, so extract a module). |
| Reliable sync with the family's real calendars | Via HA calendar entities | In Preview this is simulated by Local Calendar. |

#### Differentiators in the category

| Feature | Status | Notes |
|---------|--------|-------|
| Local-only, no subscription, no vendor lock-in (Hearth cancels lock you out of lists and chores; Skylight paywalls photos and meal planner) | Core design | A real selling point to say to the family: nothing disappears if we stop paying. |
| Deep HA integration (automations, device triggers, presence, timers on speakers) | Validated | Beyond what appliance-style products offer. |
| Drag-to-reorder meals in Month view | Backlog | Polish. Already works in Week view Edit mode. Value is moderate: Month view is for overview, and moving a meal is rare. Complexity MEDIUM (calendar card monolith). Let her rank it. |
| Finish the Theme Builder panel | Backlog | DAKboard sells customisation. 10 built-in themes plus the selector already deliver most of the value. Complexity MEDIUM-HIGH because it is unfinished and undocumented. Lowest priority unless she asks. Note: it doubles as the cheap way to make Preview visually distinct. |
| Photo screensaver from a local folder or HA media | Unknown whether the existing screensaver does photos | Check before proposing. A common wish for a wall display. LOW-MEDIUM. |
| School or club calendar import via ICS (HA Remote Calendar) | Not part of this fork | Cloud-free equivalent of Skylight Magic Import. Mostly HA setup, not code. Candidate for later. |
| Notification-first display (show only what matters now) | Partly (Right Now bar, Today card) | HA community interest. Already covered. |

#### Anti-Features in the category

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| AI paper-schedule scanning (Skylight SideKick style) | Looks magical in marketing. | Needs a cloud model or heavy local model; contradicts the local-only constraint. | Manual entry plus ICS import for school calendars. |
| Subscription tiers or feature gating | Common business model. | Not relevant, and the family's advantage is that nothing is paywalled. | None. |
| Everything-on-one-screen dashboards with hundreds of HA entities | Impressive demo. | Cluttered; HA community itself argues wall tablets work better showing only what matters. | Keep Family Hub screens focused. Link to other dashboards separately. |
| Chat, family files, social features (for example LX Family) | Feature-rich competitors. | Scope creep far beyond a calendar/chores hub. | Out of scope. |
| Heavy theme or layout editor for end users before the basics are loved | Customisation appeal. | Large unfinished surface already exists; investing before she asks is speculative. | Finish only if she ranks it highly. |

---

## Feature Dependencies

```
Dev environment (Compose + demo seed)
    └──requires──> Scripted seed data (date-relative)
                       └──requires──> Local Calendar + Local To-do + HA users per person

Family Preview (separate always-on HA instance)
    ├──requires──> Dev environment (same seed + deploy tooling)
    ├──requires──> Isolation (null notify target, no real calendars, no real speakers)
    ├──requires──> Non-admin user + Family-Hub-only dashboard (sidebar/kiosk handling)
    └──requires──> deploy-preview from branch

reset-preview ──requires──> Scripted seed data

Her access (Companion app / home-screen icon) ──requires──> Preview reachable on stable address
                                                       └──requires──> Remote-access decision (Wi-Fi only vs Tailscale / Nabu Casa)

PREVIEW visual distinction ──enhances──> Her access (avoids Home/Preview mix-up)
Version stamp in UI ──enhances──> UAT (proves which build she is on)

Getting started guide ──requires──> Working Preview + seed data (screenshots come from it)
Playwright before/after screenshots ──requires──> Seed data + test harness
What's new ──requires──> Release-to-Home step; ──enhanced by──> screenshots

Family request template (exists) ──feeds──> Acceptance criteria (I do / I see)
    └──feeds──> Build in Dev ──> deploy-preview ──> Her UAT ──> Sign-off gate ──> Tagged release ──> Home
                                                                                        ├──requires──> Fork versioning decision
                                                                                        ├──requires──> HA backup + rollback plan
                                                                                        └──produces──> What's new entry

Candidate backlog:
    Edit existing event ──requires──> Extract module from calendar card (no tests yet → harness first)
    Month-view meal drag ──requires──> Extract module from calendar card; ──requires──> JS smoke tests
    Theme Builder finish ──enhanced by──> Preview distinct-theme need (small overlap only)

Conflicts:
    Self-updater on Home ──conflicts──> Sign-off gate and tagged-release flow
    Real-data copy into Preview ──conflicts──> Safety constraint
```

### Dependency Notes

- **Preview requires isolation checks, not just a separate instance.** A separate HA volume prevents data crossover, but the poller, notify targets, TTS and Companion-app notify services can still reach real devices. Treat "nothing leaves the house network" as an explicit acceptance test.
- **Getting started guide requires a working seeded Preview.** Write it after the first she-can-use-it milestone, with screenshots generated from seed data so they can be regenerated after each change.
- **Release to Home requires the versioning decision.** The manifest and changelog already disagree upstream (1.168.85 vs changelog stopping at 1.135.4). Choose a scheme in the foundation phase, because every later tag depends on it.
- **Backlog items that touch the calendar card depend on the safety net.** The card is about 31k lines with no tests, so smoke tests and module extraction come first.
- **Sign-off gate is a rule, not a tool.** It can ship on day one as a checklist, with automation (labels, PR checks) added only if it proves useful.

---

## MVP Definition

### Launch With (first she-can-use-it milestone)

- [ ] Seeded, date-relative Preview data plus `reset-preview` — without realistic data there is nothing to judge
- [ ] Always-on Preview on a stable address, isolated from real calendars, notifications and speakers — core safety promise
- [ ] Non-admin user for her, with a Family-Hub-only dashboard and sidebar handled — "feels like an app, not a dev tool"
- [ ] One-tap access on her phone (Companion app or home-screen icon) with a clear PREVIEW signal — avoids Home/Preview confusion
- [ ] `deploy-preview <branch>` — needed for the first visible trivial change
- [ ] Getting started guide with screenshots in `docs/family/` — onboarding for her
- [ ] Family request template (exists), with "I do / I see" acceptance criteria wording and a three-answer UAT outcome
- [ ] Sign-off checklist before any release to Home

### Add After Validation (once she has used the loop once or twice)

- [ ] Version stamp in the UI — when "did it refresh?" confusion actually appears
- [ ] Playwright before/after screenshots — once the test harness exists
- [ ] Tagged-release flow to Home with `RELEASING.md`, HA backup and rollback rehearsal — before the first real release to Home
- [ ] `docs/family/whats-new.md` — with the first release to Home
- [ ] Wall-tablet kiosk trial in Preview — after phone flow is comfortable
- [ ] Her ranking of the backlog (event editing, meal drag, Theme Builder, whatever surfaces in week one)

### Future Consideration

- [ ] In-app "What's new" card — only if the doc alone is not noticed
- [ ] Seed scenarios (busy Saturday, empty week) — when demoing edge cases matters
- [ ] ICS school-calendar import, photo screensaver — if she asks
- [ ] Finish and document Theme Builder — if she ranks it high

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Date-relative seed data + reset | HIGH | MEDIUM | P1 |
| Preview isolation (no real notifications / speakers / calendars) | HIGH | MEDIUM | P1 |
| Always-on Preview + deploy-preview | HIGH | MEDIUM | P1 |
| Her non-admin, Family-Hub-only access | HIGH | MEDIUM | P1 |
| One-tap phone access + PREVIEW signal | HIGH | LOW | P1 |
| Getting started guide | HIGH | LOW | P1 |
| "I do / I see" criteria + sign-off checklist | HIGH | LOW | P1 |
| Tagged release to Home + backup/rollback | HIGH | MEDIUM | P1 (before first Home release) |
| What's new per release | MEDIUM | LOW | P1 (with first release) |
| Version stamp in UI | MEDIUM | LOW | P2 |
| Playwright before/after screenshots | MEDIUM | MEDIUM | P2 |
| Wall-tablet kiosk trial | MEDIUM | MEDIUM | P2 |
| Edit existing calendar event | HIGH (probable) | MEDIUM | P2, her call after week one |
| Month-view meal drag-to-reorder | LOW-MEDIUM | MEDIUM | P3, her call |
| Finish Theme Builder | LOW | MEDIUM-HIGH | P3, her call |
| In-app What's new card | LOW | MEDIUM | P3 |
| Seed scenarios | LOW | MEDIUM | P3 |

**Priority key:** P1 must have for the Preview milestone; P2 should have, add when possible; P3 nice to have.

---

## Competitor Feature Analysis

| Feature | Skylight | Hearth | DAKboard / TouchHub | Our Approach |
|---------|----------|--------|---------------------|--------------|
| Core calendar and chores | Free with device | Membership-gated | Calendar free; chores manager on paid plans | Already built, free, local |
| Rewards | Paid extra | Part of routines | Paid chores manager | Already built (stars, rewards) |
| Meal planner | Plus subscription | Not confirmed | Not confirmed | Already built |
| Photo screensaver | Plus subscription | Shared moments | Core feature | Verify existing screensaver; optional |
| Paper-schedule AI (SideKick, Magic Import) | Paid | Not confirmed | Not applicable | Do not build (cloud); ICS import if wanted |
| Hardware | Closed, dedicated | Dedicated | Bring your own screen | Bring your own tablet (Fully Kiosk or Companion) |
| Child lock | Yes | Per-child profiles | Yes (TouchHub) | Already built (PIN, child accounts) |
| Lock-in risk | Subscription features vanish | Cancelling locks lists, chores, routines | Plan-gated | None: local, GPLv3 |

## Sources

- Skylight reviews and brand response: [NBC Select Skylight review](https://www.nbcnews.com/select/shopping/skylight-brand-review-rcna601728), [Skylight Calendar Max reviews](https://shopsavvy.com/products/skylight-calendar-max), [Blesser House family review](https://www.blesserhouse.com/our-family-tried-the-skylight-calendar-heres-what-we-loved-didnt/comment-page-2). Confidence LOW-MEDIUM (affiliate and retailer content; subscription prices conflict between sources: $39 Plus per Skylight's own reply versus $79 in others).
- Hearth and DAKboard: [DAKboard vs Hearth](https://dakboard.com/c/comparisons/dakboard-vs-hearth/), [DAKboard vs Skylight](https://dakboard.com/c/comparisons/dakboard-vs-skylight/), [Hearth Display review](https://wetried.it/hearth-display-review-digital-calendar-organizer/), [DAKboard TouchHub](https://blog.dakboard.com/meet-touchhub-bring-order-to-the-daily-family-shuffle/). Confidence LOW (vendor-authored comparisons; Hearth rewards, screen time and meal planner not confirmed).
- HA community family boards: [LX Family self-hosted family board](https://community.home-assistant.io/t/lx-family-a-self-hosted-family-board-with-calendars-chores-kid-profiles-and-home-assistant-widgets/1020587), [Are we thinking about wall tablets the wrong way?](https://community.home-assistant.io/t/are-we-thinking-about-wall-tablets-the-wrong-way/1019690). Confidence MEDIUM.
- HA Companion app multi-server: [iOS multi-server](https://www.home-assistant.io/blog/2021/12/18/ios-multi-server), [Android 2023.3 multiple servers](https://home-assistant.io/blog/2023/03/30/android-20233), [Companion app docs](https://companion.home-assistant.io/docs/getting_started/). Confidence MEDIUM-HIGH (official). Community reports of the app opening the wrong server after a reset are anecdotal.
- Kiosk and non-admin users: [kiosk-mode (matt8707)](https://github.com/matt8707/kiosk-mode), [Kiosk mode forum thread](https://community.home-assistant.io/t/kiosk-mode/425678/28), [wall tablet guides](https://smarthome.yoavmor.com/home-assistant/controlling-your-home-assistant-dashboard-with-a-wall-mounted-tablet/), [Android tablet kiosk problems](https://community.home-assistant.io/t/android-tablet-kiosk-problems/991354). Confidence MEDIUM. No single authoritative non-admin kiosk recipe found; verify on the HA version used.
- Local Calendar and Local To-do (seed targets): [Local calendar](https://home-assistant.io/integrations/local_calendar), [Local to-do](https://home-assistant.io/integrations/local_todo). Confidence HIGH (official). A seeding script approach was not found documented and needs phase-level research.
- UAT and release-note practice: [UAT guide (Lovable)](https://lovable.dev/en/guides/user-acceptance-testing-guide), [UAT format reference](https://tessl.io/registry/testland/manual-test-script-author/files/references/uat-format.md), [Release notes best practices (Archbee)](https://archbee.com/blog/release-notes-best-practices), [ProductPlan release notes](https://www.productplan.com/release-notes-best-practices). Confidence MEDIUM-LOW (generic vendor blogs, adapted to a household).
- Repo context: `/home/user/HA-Family-Hub/.planning/PROJECT.md`, `/home/user/HA-Family-Hub/DOCUMENTATION.md` (To Do / Ideas, lines ~735-755), `/home/user/HA-Family-Hub/.github/ISSUE_TEMPLATE/family_request.md`. Confidence HIGH.

---
*Feature research for: HA family-hub dashboard fork with family-led Preview/feedback/release workflow*
*Researched: 2026-10-26*
