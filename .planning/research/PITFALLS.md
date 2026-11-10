# Pitfalls Research

**Domain:** Customising a forked Home Assistant custom integration (HACS, vanilla-JS Lovelace cards, 13k-line `__init__.py`, no tests) with a Dev / Family Preview / Home environment split and a non-technical product owner
**Researched:** 2026-10-26
**Confidence:** MEDIUM overall. Items tagged `[repo]` were verified by reading or running checks against this repository (HIGH). Items tagged `[HA docs]` come from fetched Home Assistant or HACS documentation (HIGH/MEDIUM). Items tagged `[HA knowledge]` rest on general Home Assistant behaviour that was not re-verified against a live instance today (MEDIUM). Items tagged `[verify]` need a quick spike before the roadmap relies on them.

Existing concerns already catalogued in `.planning/codebase/CONCERNS.md` (monolith, duplicate cards, `.pyc`, Grocy key, `innerHTML`, updater, broad `except`) are not re-derived here. They appear only where they interact with the new work.

Phase key: **1** Clean foundation, **2** Dev + Family Preview, **3** Safety net (tests/CI), **4** Family-led customisation loop.

---

## Critical Pitfalls

### Pitfall 1: Preview HA shares an identity with Home HA

**What goes wrong:**
The Companion app, mDNS discovery and (optionally) Nabu Casa treat the two servers as one, or as two indistinguishable servers. She taps "Home Assistant" in the app and edits the real family hub, or the Companion app silently re-points the real server entry at Preview.

**Why it happens:**
The fastest way to build Preview is to copy Home's config directory, which also copies `.storage/core.uuid`, the instance name and the auth store. Two instances with the same instance UUID are treated by the mobile app as the same server. Even with a fresh config, both advertise `_home-assistant._tcp` with the default name "Home", and the app's auto-discovery list shows both. `[HA knowledge]`

**How to avoid:**
- Never clone Home's `config/`. Preview starts from an empty config volume and is onboarded by script (onboarding API creates the first user) so it gets its own `core.uuid`.
- Give Preview a loud identity: `homeassistant: name: "Family Hub PREVIEW"`, a distinct theme/primary colour, a different default dashboard title, and a different Companion app server name.
- Use a different host port (for example 8124) or a different hostname, and use bridge networking with an explicit port mapping rather than `network_mode: host`, which both collides on 8123 and exposes the instance to LAN discovery.
- Do not log Preview in to the same Nabu Casa account as Home (one cloud remote-UI per account). Use home Wi-Fi, a LAN hostname, or Tailscale for remote access.
- Record the Preview URL as a bookmark/kiosk URL in the family guide so she never has to "pick a server".

**Warning signs:**
The Companion app shows only one server after adding Preview; both servers show the same name; `core.uuid` is identical in both config volumes; she asks "which one am I in?".

**Phase to address:** 2

---

### Pitfall 2: Preview notifications, timers and reminders reach real phones and speakers

**What goes wrong:**
A seeded "dinner at 6pm" event with a reminder fires from Preview's 5-minute backend poller and pushes a notification to a real family phone, or a seeded timer rings a real speaker. The family cannot tell the Preview notification from a real one and acts on fake data.

**Why it happens:**
The integration auto-discovers `notify.mobile_app_*` targets per HA user (see `__init__.py` around line 1971) and fires `notify.*` calls from a poller. As soon as her phone logs in to Preview through the Companion app, a `notify.mobile_app_<phone>` service exists in Preview and is picked up. Companion push goes through Home Assistant's push relay, which works for any server the app is registered with. If Preview runs with host networking it can also discover real Cast/Sonos/media players. `[repo]` for discovery, `[HA knowledge]` for relay behaviour.

**How to avoid:**
- Decide before seeding: Preview notification targets are `notify.persistent_notification` or a Preview-only notify test target, and the integration's per-person notify mapping in the seed script is set explicitly rather than left on auto-discovery.
- Name the Companion app device on Preview "Preview - <name>" so `notify.mobile_app_preview_<name>` is unmistakable, and put "[PREVIEW]" in the title of any notify the reminder code can be configured to prefix.
- Bridge networking only; no media_player, Cast, Sonos, Zeroconf-discovered integrations installed in Preview. Disable `default_config` discovery components (`ssdp`, `zeroconf`, `dhcp`, `bluetooth`) in Preview's `configuration.yaml`.
- Seed reminders only for events whose reminder time is already past or far in the future, or seed with reminders disabled, then enable them for one deliberate "notification test" step in UAT.
- Add an automated check to `deploy-preview`/`reset-preview`: list `notify.*` and `media_player.*` services in Preview and fail if anything other than the allow-list exists.

**Warning signs:**
Her phone buzzes with a calendar reminder for an event nobody created; Preview log shows `notify.mobile_app_*` calls; Preview entity list contains any media_player.

**Phase to address:** 2 (design), 4 (re-check every time a notification feature is changed)

---

### Pitfall 3: `reset-preview` is defeated by the integration's own backup-and-restore, and by HA's write-on-shutdown

**What goes wrong:**
`reset-preview` wipes `.storage/` and restarts, but chores, rewards, permissions and Settings reappear from before the reset. Or the seed script edits `.storage/*` while HA is running and the changes vanish (or corrupt) when HA writes its in-memory state back on stop.

**Why it happens:**
`store.py` writes durable backups to `<config>/family_hub_backups/` (outside `.storage/` and outside the integration folder), and `_maybe_restore_backup` restores them whenever a Store loads completely empty, by design "because the entry was removed and re-added". A reset that only deletes `.storage` therefore resurrects old data. Separately, HA keeps most Stores in memory and flushes them on a delayed write and at shutdown, so editing `.storage` on disk under a running instance is overwritten. `[repo]` for the backup mechanism, `[HA knowledge]` for write-on-stop.

**How to avoid:**
- `reset-preview` must `docker compose down` first, delete the entire config volume (or at minimum `.storage/`, `family_hub_backups/`, `home-assistant_v2.db*`, and any `*.ics` Local Calendar/To-do data), then bring up and re-seed from scratch. Test the command by seeding, changing data, resetting, and asserting the seeded state is back byte-for-byte equivalent.
- Seed through public interfaces while HA is running, not by hand-writing `.storage` files: onboarding API, REST/WebSocket `config_entries/flow` for Local Calendar and Local To-do, `calendar.create_event`, `todo.add_item`, `config/auth/create`, and the integration's own `family_hub/...` websocket commands and 8 services for chores/rewards/people. This survives HA storage schema changes between releases.
- If a raw `.storage` template is ever used (fast path), key it to a pinned HA version and only write it while HA is stopped.
- The same applies to Dev if its config is a bind mount: Dev reset must also clear `family_hub_backups/`.

**Warning signs:**
Data present after reset that the seed script does not create; log line "this install's ... store was empty, so it was restored from the backup"; a second `reset-preview` run produces different results from the first.

**Phase to address:** 2

---

### Pitfall 4: Seed data goes stale because it was written with absolute dates

**What goes wrong:**
The "realistic week" looks great on day one and is empty or in the past a week later. She opens Preview, sees nothing on Today, and concludes the app is broken or that the change did not work. Recurring-chore and week-rollover logic is never exercised.

**Why it happens:**
Seed files are authored as fixed ICS/JSON. Preview is "always-on", so real time keeps moving. Local Calendar timezone and DST edges also differ if Preview's `time_zone` is not Home's. `[HA knowledge]`

**How to avoid:**
- Generate every event, chore due date and meal relative to "today" in the seed script (Monday of the current week plus offsets), in Preview's configured time zone, which must equal Home's.
- Make `reset-preview` idempotent and cheap (under a minute), and schedule it weekly (cron/systemd timer) outside the hours she uses it, or add a documented "refresh my week" command she can trigger. Announce the schedule in the family guide so a weekly reset never surprises her mid-test.
- Include seed cases for the awkward paths: all-day events, multi-day events, recurring events across a month boundary, an overdue chore, a chore due "now", a reward she can afford and one she cannot, a child account.
- Seed Local Calendar and Local To-do only; but add one seeded case matching how Home's real calendars actually work (see Pitfall 11).

**Warning signs:**
Today card empty on a Monday; seeded events all in the past; Month view looks fine but Week view is blank.

**Phase to address:** 2, revisited in 4

---

### Pitfall 5: The card is not found on a fresh Preview (best-effort resource registration silently no-ops)

**What goes wrong:**
Her very first look at Preview shows "Custom element doesn't exist: family-week-calendar-card" or a blank panel. The first impression of the whole workflow is a red error box.

**Why it happens:**
`_register_dashboard_resource` uses Lovelace internal storage and is documented to "silently no-op" on any failure, including YAML-mode dashboards or a changed internal collection shape. It also only logs at debug level. The resource is registered only when `hass.data["lovelace"].resources` has `async_create_item`. A fresh Preview with a YAML-defined or not-yet-created dashboard hits the no-op branch. `[repo]`

**How to avoid:**
- The seed step must create the dashboard (storage mode), add the card resources through the supported WebSocket command `lovelace/resources/create` if missing, and then verify by reading `lovelace/resources` back and asserting every one of the 14 served URLs is listed. Fail the deploy if not.
- Also verify served content: `GET /family_hub_card/family-week-calendar-card.js?v=<hash>` returns 200 and the hash equals the hash of the repo file.
- Raise the "could not auto-register" log from debug to warning when touching this code (small change, large diagnostic value).
- Seed a kiosk dashboard that uses each card once, so the "smoke test by eye" is one page.

**Warning signs:**
Browser console "Custom element doesn't exist"; `lovelace/resources` list missing `family_hub_*` entries; HA log silent.

**Phase to address:** 2

---

### Pitfall 6: She tests, but she is looking at old JavaScript (WebView / kiosk caching), and nobody can tell

**What goes wrong:**
Developer deploys a visible change, she opens the app, sees nothing different, and either reports "you didn't do it" or silently signs off on the previous behaviour. UAT answers become meaningless. On the Home wall tablet, an always-open page keeps running JS from weeks ago.

**Why it happens:**
Cache-busting here is a content-hash `?v=` suffix on the Lovelace resource URL, and it only takes effect when (a) the resource entry was successfully updated (Pitfall 5) and (b) the page reloads and re-reads the resource list. Companion app WebViews and Fully Kiosk-style wall tablets keep a long-lived page; ES module import caches live for the page lifetime; cards only poll data every 60s, not code. Module-level `customElements.define` also throws "already defined" if two resource entries with different URLs load the same card. `[repo]` for hash/registration, `[HA knowledge]` for WebView behaviour.

**How to avoid:**
- Show a build stamp in the UI: the card version and content-hash in a small footer (or Settings > About) and in `console.info` on load. Every UAT step starts with "check it says build abc123".
- `deploy-preview` ends by printing the served hash and the expected hash and telling the developer "ask her to pull-to-refresh / reopen the app" until she has confirmed the stamp.
- Document the refresh gesture per device in the family guide (pull-to-refresh; Companion app "reset frontend cache" under app debugging settings; tablet kiosk reload). Configure the Preview kiosk tablet to reload on a schedule or on screen-on.
- Do not hand-add card resources in Preview or Dev if the integration also manages them; duplicate entries cause double-define errors.

**Warning signs:**
Her screenshot has the old layout; stamp differs from deploy output; console shows "has already been used with this registry".

**Phase to address:** 2 (stamp, refresh guide), 4 (enforced step in the loop)

---

### Pitfall 7: Deleting the root-level duplicates destroys information, or leaves the door open for the next upstream sync to re-create them

**What goes wrong:**
Two failures. (a) A root copy contained something not in the served copy and it is deleted unread. (b) Upstream's next commit, made via GitHub web "Add files via upload" into the root again, either conflicts (modify/delete) or lands unnoticed in dead files while the developer believes it was merged.

**Why it happens:**
The duplicates exist because the upstream author's workflow uploads files to the wrong folder; the latest upstream commit (`8f7172d`, 2026-10-25) again touched root `de/en/es.json` and root `family-hub-*` cards. Counting differing lines shows every root copy has root-only lines (for example 2,531 in the calendar card, 269 in the chores card, 254 in the recipe box) and several root-only translation keys exist (`fh_ui.settings.chore_due_label`, `goals_in_chores_*`, `small_screen_mode_hint`, `date_only`) that appear in no served card and no `translations/` file. `[repo]` Either these are stale remnants or they are the upstream author's newest unfinished work.

**How to avoid:**
- Before deleting, produce one reviewed diff per root file against its served counterpart and note root-only keys. A 30-minute triage, recorded in the phase summary, converts "probably stale" to "verified stale". Port anything wanted into `card/`, `panel/` and `translations/`.
- Add a CI check (Phase 3) that fails when any `custom_components/family_hub/*.js` or `custom_components/family_hub/{de,en,es,fr,it,nl,pl,pt,pt-BR}.json` exists outside `card/`, `panel/`, `translations/`.
- Add an `upstream` git remote and adopt a written policy: no routine merges; selective cherry-picks, with each upstream change classified. When cherry-picking an upstream change that touched a root copy, port it by hand into the served file.
- Do deletion as its own commit with no other changes, so it is a one-line revert.

**Warning signs:**
`git diff upstream/main` shows changes only in root-level files; a fix "doesn't work" after merge; reviewers see a changed `.js` that is not under `card/` or `panel/`.

**Phase to address:** 1 (triage and delete), 3 (CI guard)

---

### Pitfall 8: Moving translations "by key parity" and breaking what HA actually loads

**What goes wrong:**
The move looks correct (keys match) but strings still show English, or HA drops them, or hassfest later rejects the file, or a translated language is missing for pt/pt-BR users.

**Why it happens:**
- HA loads only `translations/<lang>.json` for custom integrations; `strings.json` is not used by custom integrations at all, and English at `translations/en.json` is the mandatory fallback. A translation whose `{placeholders}` differ from English is silently dropped in favour of English. `[HA docs]`
- This project's UI strings live under a non-standard top-level category `fh_ui` (renamed from `frontend`, which collides with HA's own namespace) and are fetched by cards through `hass.loadBackendTranslation("fh_ui", "family_hub")`. Anything that renames, nests or restructures that category breaks every card silently, because the card falls back to hard-coded English with only a `console.warn`. `[repo]`
- The five root files (`it`, `nl`, `pl`, `pt`, `pt-BR`) have exactly the same 2,139 leaf keys as `translations/en.json`; so parity is not the real risk. The real risks are: `strings.json` (566 keys, includes an HTML string `reminders_hint_html`) is dead but looks authoritative; `translations/en.json` itself has strings with leading/trailing spaces or URLs (for example `fh_ui.nav.edit_suffix`) that hassfest's string rules reject; and the cards use custom `%0%`/`%n%` placeholders where 16 non-English strings intentionally differ from English (plural slot removed), which a naive "placeholder parity" check will flag as errors. `[repo]`
- HA picks the file by exact language code (`pt-BR` does not fall back to `pt`; both exist today). `[HA knowledge]`

**How to avoid:**
- Move the five files with `git mv`, then write the parity script once and keep it in the repo: compare leaf keys against `translations/en.json`, compare `{brace}` placeholders (hard fail), compare `%n%` placeholders (report-only with an allow-list of the 16 intentional differences), and fail on JSON syntax errors.
- Delete root `de/en/es/fr.json` (verified truncated, 1,019 and 1,117 keys) and decide `strings.json`: delete it (custom integrations never read it), noting this in the commit.
- Do not touch the `fh_ui` category name, nesting depth or key naming in this phase.
- Verify in a running Dev HA after restart: set HA user language to `nl` and to `pt-BR` and confirm the Month/Week labels change. Translation caches survive until HA restart, so test after a full restart, not a reload.
- Remember the README advertises nine languages; update README only after the Dev check passes.

**Warning signs:**
Console `[family_hub] failed to load "<lang>" translations - staying on English fallback text`; German works but Dutch does not; HA log "Validation of translation placeholders for localization ... failed".

**Phase to address:** 1 (move and check), 3 (parity script in CI)

---

### Pitfall 9: Renaming "fork identity" goes too far, or not far enough

**What goes wrong:**
Too far: changing `domain`, service names, `family_hub/...` websocket prefixes, card element names or the `fh_ui` category orphans the config entry, all saved dashboards, device triggers, automations and Stores keyed to the entry. Not far enough: Home's HACS still tracks upstream `JVarhol/HA-Family-Hub`, so "Update" installs upstream code over the fork, or issues and links keep going to upstream.

**Why it happens:**
"Make it ours" is applied to everything with the old name. HACS identifies a custom repository by its GitHub repo, so changing `documentation` in `manifest.json` does nothing to what Home's HACS is actually tracking. `[HA knowledge]`

**How to avoid:**
- Change only: `manifest.json` `documentation`, `issue_tracker`, `codeowners`; README badges and links; HACS install instructions; docs site config. Leave `domain: family_hub`, `name`, all runtime identifiers and card tags untouched. Credit upstream in README and keep `LICENSE` (GPLv3) and licence headers.
- For Home: remove the upstream custom repository from HACS and add `Future-Bridge-AI/HA-Family-Hub`, then redownload. Config entries and Stores survive because the domain is unchanged. Do this once, on Home, as a deliberate documented step, after taking a full HA backup.
- Verify no other HACS entry or manual copy of `custom_components/family_hub` is still present (two copies is a classic cause of "my change does nothing").
- Replace the `@bordello_labs` codeowner with the fork owner's real GitHub handle (hassfest requires `@`-prefixed GitHub handles).

**Warning signs:**
Home HACS shows the upstream author's repo; "Update available" appears for a version number that does not exist in the fork; entities disappear after an edit to `domain`.

**Phase to address:** 1 (manifest/docs), 2 (cut-over of Home's HACS source before the first release)

---

### Pitfall 10: Versioning and HACS update detection (no tags, no releases, regressing version)

**What goes wrong:**
HACS never offers the update, offers the wrong one, or installs from the default branch tip (an untested commit) onto Home. A rollback is impossible because there is nothing to roll back to.

**Why it happens:**
The fork has no git tags and no GitHub Releases. HACS prefers releases, shows the five latest plus the default branch, and with no releases installs whatever is on the default branch. HACS compares versions semantically, so adopting a lower or non-monotonic number looks like a downgrade and no update is offered. Manifest says 1.168.85 while the changelog stops at 1.135.4. `[HA docs]` for release behaviour, `[HA knowledge]` for comparison and refresh delay.

**How to avoid:**
- Decide in Phase 1: continue upstream numbering, strictly increasing (suggest `1.169.0` for the first fork release; mark the fork lineage in the changelog, not in the version string). Avoid `+` and unusual suffixes; keep to plain dotted numbers HA's version parser accepts.
- Every release to Home is a GitHub Release whose tag equals `manifest.json` version (for example `v1.169.1`, with the manifest saying `1.169.1`). A release script (or CI job) bumps the manifest, tags, and refuses if the manifest, `CHANGELOG.md` and `website/docs/changelog.md` disagree.
- `main` is never what Home installs: Home uses releases only, Preview uses `deploy-preview <branch>`. This makes "Home only receives changes she signed off" mechanically enforced, not a convention.
- HACS caches repository data for a while; after publishing, use HACS "Update information" before concluding detection is broken.
- Keep the release tag list as the rollback menu: rollback is "redownload previous tag" and must be rehearsed once on Preview.

**Warning signs:**
HACS shows the commit sha instead of a version; "Download" lists only "Default branch"; manifest and latest tag differ.

**Phase to address:** 1 (scheme decision), 3 (CI check), 4 (release step)

---

### Pitfall 11: Preview is not Home, so "works in Preview" is not "works at Home"

**What goes wrong:**
She signs off in Preview and the release breaks the real family setup, which is exactly the outcome the project exists to prevent.

**Why it happens:** Parity gaps that are easy to miss:
- **HA version drift.** Preview pulled `latest` while Home runs an older (or newer) core. The integration uses non-public APIs (Lovelace storage collection, `async_sign_path`, `homeassistant.components.calendar.const.DATA_COMPONENT`, `local_todo` service calls) that change between monthly releases. `[repo]`
- **Calendar and to-do providers.** Preview uses Local Calendar and Local To-do; Home may use Google/CalDAV/iCloud calendars with different editability, time zones, recurrence expansion and slower responses. `[repo]` (runtime requirements listed in PROJECT.md)
- **Transport.** Preview over `http://<ip>:8124` has no secure context; Home is probably HTTPS. Clipboard, service workers, some browser APIs and Companion behaviours differ. `[HA knowledge]`
- **Hardware.** She tests on a phone; the 1.7 MB calendar card must run on a low-power wall tablet.
- **Data shape and migration.** Preview is seeded fresh in the newest schema; Home holds months of old-shape Store data. Rollback after a schema write by new code can leave old code unable to read it.
- **Dashboard rewriting.** The integration rewrites saved dashboards on startup (`_migrate_my_chores_cards`), so Home's existing dashboards are mutated by an upgrade in ways a clean Preview never exercises.

**How to avoid:**
- Pin the HA image tag in both Dev and Preview to exactly Home's running version, recorded in one `versions.env`. Upgrade Home's HA and Preview together, never one without the other.
- Capture a sanitised export from Home (the integration's settings-history export, or `.storage/family_hub*` with names changed) as a "home-shaped" fixture that Preview can be loaded with for an **upgrade rehearsal** before each Home release. Do not commit it (see Security Mistakes).
- Add a Home-parity checklist to the release step: HA version equal, the same calendar provider type exercised at least once by the developer on Home in read-only fashion, wall tablet smoke test after release.
- Take a full HA backup immediately before each Home release; know where `family_hub_backups/` is.

**Warning signs:**
Preview `ha core info` version differs from Home's; sign-off passed but the wall tablet shows a stale or broken page; Home log shows `KeyError` on settings keys.

**Phase to address:** 2 (pinning), 4 (rehearsal and checklist in the loop)

---

### Pitfall 12: Bootstrapping `pytest-homeassistant-custom-component` against the monolith

**What goes wrong:**
Day-one tests fail for environmental rather than behavioural reasons: "Integration 'family_hub' not found", missing Python modules for `image_upload`/`file_upload`, `hass.http` missing, lingering timers/threads failures, or an import error caused by the plugin's HA version being newer than the declared minimum. The harness is declared "too hard" and abandoned before any engine test exists.

**Why it happens:**
- The plugin tracks the latest HA release (updated with each core release) and is pinned to one HA version and its Python and pytest versions. Local Python and CI Python must match what that HA version needs. `[HA docs]` (PyPI notes), `[verify]` exact pin today.
- The custom integration must be enabled via the `enable_custom_integrations` fixture (usually an autouse fixture in `conftest.py`), and `custom_components/` must be importable from the test root. Without it, HA reports the integration cannot be found. `[HA docs]`
- Importing any submodule (for example `custom_components.family_hub.chore_engine`) first executes the 13k-line `__init__.py`, which imports `homeassistant.components.http.StaticPathConfig`, `calendar.const.DATA_COMPONENT`, `panel_custom`, aiohttp, and defines import-time constants. A version-specific import error therefore fails even "pure" engine tests. `[repo]`
- Full `async_setup_entry` pulls in dependencies `frontend`, `http`, `lovelace`, `file_upload`, `image_upload` (image processing libs), registers static paths on `hass.http`, starts a 5-minute poller and `Store` delayed writes. The plugin's cleanup check fails the test for any lingering timer/task. `[HA knowledge]`
- Time-sensitive engines (week rollover, recurring chores) behave differently with naive vs timezone-aware datetimes and with the sandbox's UTC default.

**How to avoid:**
- Order the work: (1) get one trivial test importing `chore_engine` green in CI on the pinned HA/Python; (2) pure engine tests using plain data; (3) config-flow and websocket tests with mocked dependencies; (4) only then a thin `async_setup_entry` smoke test using `mock_integration`/patches for the `http`/`frontend` dependencies. Do not start with a full-setup test.
- Commit a `requirements_test.txt` pinning `pytest-homeassistant-custom-component` and a `.python-version`/CI matrix to match it. Add a scheduled CI job against HA beta to see breakage early, non-blocking.
- Write characterisation tests: assert what the code does today (golden outputs), including its quirks. Do not fix bugs in the same change as adding the test that documents them.
- Use `freezegun`/the plugin's time helpers and set `hass.config.time_zone` explicitly; add cases at week boundary, month boundary and DST change.
- Always unload the config entry at test end (`await hass.config_entries.async_unload(...)`) so the poller and Stores are cleaned up.
- Do not set a global coverage gate on 28k lines; gate "no decrease" or per-module thresholds on engines only.
- Fix the declared minimum HA version at the same time (Pitfall 14), because tests only prove behaviour on the pinned latest.

**Warning signs:**
`ModuleNotFoundError` for `PIL`/`hass_frontend`; "Lingering timer" failures; tests pass locally and fail in CI due to Python minor version; `ImportError: cannot import name ... from homeassistant.components...`.

**Phase to address:** 3

---

### Pitfall 13: hassfest and the HACS action fail on day one, and the team either disables them or chases them for a week

**What goes wrong:**
The first CI run is red on checks that have nothing to do with the new work. People set `continue-on-error` forever, or contort translations/manifest to satisfy a rule without understanding it.

**Why it happens (specific to this repo):**
- **Manifest key order.** Hassfest expects `domain`, `name`, then keys alphabetically. Current manifest has `dependencies` before `after_dependencies` and `codeowners`/`config_flow` before it, so ordering likely fails. `[repo]` + `[HA knowledge]`
- **Non-standard translation category `fh_ui`.** Hassfest validates `translations/en.json` against a fixed schema; an unknown top-level key `fh_ui` is likely rejected, as are strings with leading/trailing spaces, URLs or HTML (found in `translations/en.json`, for example `fh_ui.nav.edit_suffix`, `config.step.grocy.data.grocy_url`). `[HA docs]` for string rules, `[verify]` for the `fh_ui` rejection.
- **Services.** 8 services in `services.yaml`; `translations/en.json` has no `services` section. Hassfest's services check may demand names/descriptions there. `[verify]`
- **Dependencies check.** Imports from `homeassistant.components.calendar`, `panel_custom`, `todo`, `local_todo` that are not declared in `dependencies`/`after_dependencies` can be flagged. `[verify]`
- **HACS action on a fork.** The HACS validation checks that the repository has a description, topics, issues enabled, a README and a `brand/` folder with `icon.png`. Forks start with issues disabled and with no description or topics copied. The `brand/` folder exists here already. `[HA docs]` for brand and manifest requirements, `[HA knowledge]` for the fork defaults.
- `hacs.json` declares `homeassistant: 2024.1.0`, but the code uses `StaticPathConfig` / `async_register_static_paths`, which I believe only exist from mid-2024 (`[verify]`). The declared minimum is therefore probably wrong.

**How to avoid:**
- Run hassfest and the HACS action once locally/in a throwaway branch in Phase 1 or the start of Phase 3 as a **spike** to produce the real list of failures, then fix by category. Do not guess.
- Enable repository Issues, add a description and topics on GitHub before the first HACS action run.
- Make validation required in two steps: first non-blocking (informational) for a short time, then blocking once green. Use `ignore:` for a single HACS check only with a written reason.
- For `fh_ui`: decide explicitly between (a) keep the category and accept a documented, narrow hassfest exception, or (b) move to a schema-valid location and change every card's `loadBackendTranslation` call together. Do not do (b) casually; it touches all 13 bundles and every translation file. Recommendation: (a) for this milestone.
- Fix the minimum HA version to the version actually tested (the pinned HA in CI and Home), in `hacs.json` and docs.

**Warning signs:**
CI red with "extra keys not allowed @ data['fh_ui']"; "Manifest keys are not sorted"; HACS "issues not enabled"/"description missing"; `continue-on-error: true` added without an issue linked.

**Phase to address:** 3 (spike early; may start at the tail of 1)

---

### Pitfall 14: Declared minimum HA version, tested version and Home's version disagree

**What goes wrong:**
`hacs.json` promises 2024.1.0; code needs something newer; tests run on the newest HA; Home runs something in between. Bugs appear only on Home.

**Why it happens:**
Nobody owns the "supported HA version". The manifest has no floor, `hacs.json` has a stale one, and the plugin pins to latest.

**How to avoid:**
One written "supported HA version" (Home's version, and the pinned CI/Preview version, ideally the same), set in `hacs.json`, README and `versions.env`. Add a CI step that fails when they disagree. Treat HA upgrades as their own small task: bump pin in Dev, run tests, bump Preview, soak, bump Home.

**Warning signs:**
Different version numbers in three places; deprecation warnings in HA logs about `register_static_path` or similar.

**Phase to address:** 1 (decide), 3 (enforce)

---

### Pitfall 15: Running UAT with a non-technical product owner: the process produces noise, not answers

**What goes wrong:**
She is shown developer artefacts (admin sidebar, repairs banners, "custom element" red boxes, Edit-dashboard mode), is asked open-ended questions ("does it look okay?"), gets a change without knowing where to find it, and gives polite approval. Alternatively she finds twelve unrelated things and the loop stalls. Sign-off becomes unreliable and she loses trust in the Preview.

**Why it happens:**
Acceptance criteria are written in developer terms. Preview is configured like a dev instance. Feedback has no channel, so requests arrive as screenshots in chat with no context.

**How to avoid:**
- Create her user as non-admin, with her own dashboard set as default, sidebar items hidden except Family Hub, no Edit access. Test exactly this configuration yourself before inviting her (log in as her user via a private window).
- Write every acceptance criterion as "do X, expect to see Y" with a screenshot of the expected result and the build stamp (Pitfall 6). Maximum three steps per criterion. UAT sessions are 10-15 minutes, one change at a time, with the developer present for the first few.
- Sign-off is an explicit yes/no per criterion plus "would you be happy if this was on the kitchen tablet tomorrow?" Record it in the phase UAT file (`gsd-verify-work`) with date and build stamp. Silence is not sign-off.
- Provide one place to send requests (the Family request issue template or a single chat thread), always paired with a screenshot of where she was.
- Keep the first win small and certain (the trivial visible change) before any real feature. Provide a "this is Preview, nothing here is real" banner on every screen she sees (Pitfall 1).
- Respect family time: do not deploy-preview during the day she is actively using it for real planning; announce deploys.
- Never ask her to read logs, run commands, or reset anything.

**Warning signs:**
Answers like "looks fine" without specifics; she uses Home instead of Preview for testing; the same confusion repeats about navigation; criteria require HA vocabulary.

**Phase to address:** 2 (setup and guide), 4 (loop discipline)

---

### Pitfall 16: Large-file and monolith edits without a safety net

**What goes wrong:**
A "small" feature (for example Month-view meal drag-to-reorder in a ~31k-line card) edits the single file, regresses an unrelated view, and nobody notices until the family does. Meanwhile new code gets appended to `__init__.py`, making Phase 3's task harder.

**Why it happens:**
Feature pressure starts as soon as Preview works; test harness is not yet in place; the card has no seams for a test.

**How to avoid:**
- Gate: no feature work on a file until the smoke test (render with mocked `hass`) and one engine test around the touched area exist. Phase 3 may overlap the end of Phase 2 but must complete before the first Phase 4 feature.
- New backend work goes into a new module (`custom_components/family_hub/<feature>.py`) registered from `async_setup_entry` with a one-line call; new card logic goes into a new file under `card/` and registered through the existing static-path pattern, not inline in the 31k-line file where avoidable.
- Keep the diff to the monolith to the minimum hook-up lines. Never run formatters (`ruff format`, prettier) across the monoliths: it makes a multi-thousand-line diff, destroys `git blame`, and makes upstream cherry-picks impossible.
- Lint adoption: start `ruff` with a minimal rule set (syntax/undefined names) and a per-file baseline; add rules gradually. Enabling the full default set on ~145 broad excepts guarantees a red CI.

**Warning signs:**
Pull requests touching `__init__.py` or the calendar card by hundreds of lines; first CI run reporting thousands of lint errors; "I'll add tests later".

**Phase to address:** 3 (gate), 4 (enforcement)

---

## Moderate Pitfalls

### Pitfall 17: Dev bind mount and the self-updater overwrite the working copy

**What goes wrong:**
Dev mounts `custom_components/family_hub` from the working copy. If anyone uses the integration's built-in "install update from zip" (`updater.py`), it extracts into the live integration directory, i.e. your git working tree, and writes backups beside it.
**Prevention:** Mount read-only where possible (or mount from a copy synced with rsync), and document that the self-updater is not used in Dev/Preview/Home (HACS or `deploy-preview` is the only install path). Consider hiding the option in Preview. Add `.gitignore` entries for any backup folder the updater creates.
**Phase:** 2

### Pitfall 18: `deploy-preview` leaves stale files and stale bytecode

**What goes wrong:** `rsync`/`cp` without delete leaves removed files (for example old root `.js` or removed Python modules) in the Preview integration folder; `__pycache__` from another interpreter persists; Python changes need a full HA restart, JS changes need a refresh.
**Prevention:** Deploy as "remove target directory, copy source, restart", excluding nothing; delete `__pycache__`; wait for HA to report started (poll `/api/` until 200) and then verify the served hash (Pitfall 5/6). Fail loudly if the branch has uncommitted changes or the build stamp doesn't change.
**Phase:** 2

### Pitfall 19: Preview "always-on" host choice (laptop vs home machine) undermines the promise

**What goes wrong:** Preview on the developer's laptop is off when she wants to try it; on a machine with the real HA's host networking, ports and discovery collide with Home.
**Prevention:** Decide early: run Preview on an always-on home machine with Docker, using a separate Compose project name, separate volumes, separate port, and `restart: unless-stopped`. If Home HA OS runs on the same hardware, use a different machine or a VM, not an add-on sharing Home's network namespace. Document backup of the Preview volume only for the seed (it is disposable).
**Phase:** 2

### Pitfall 20: Her Companion app set up on the wrong server, or in the wrong order

**What goes wrong:** She logs the app in to Preview with Home's account, or removes Home's server to "make room". Android/iOS Companion apps support multiple servers but every server registers its own device and notification entities.
**Prevention:** Add Preview as a second server (never replace Home). Use a distinct Preview user for her. Prefer a bookmarked kiosk dashboard or a pinned browser web app for Preview when Companion app complexity is not needed; the integration does not require Companion for the UI. Test the full onboarding on a spare phone first.
**Phase:** 2

### Pitfall 21: Public repo and family data

**What goes wrong:** The repo is a fork of a public project and is public. Seed data with real names, addresses, school times, a Companion token, an HA long-lived access token, Grocy API key, or screenshots from Home end up in git history.
**Prevention:** Seed uses pretend names; `docs/family/` screenshots come from Preview only; secrets via `.env` files that are gitignored (the current `.gitignore` does **not** ignore `.env`; fix in Phase 1); a pre-commit or CI secret scan. Treat the real "home-shaped" fixture (Pitfall 11) as outside the repo.
**Phase:** 1 (`.gitignore`), 2 (seed content rules)

### Pitfall 22: Untracking `.pyc` leaves them in history and in place

**What goes wrong:** `git rm --cached` is correct but forgotten steps cause the files to reappear: other branches/worktrees still track them, `.gitignore` is not in effect for already-tracked files, and the HACS zip still contains them from older tags.
**Prevention:** `git rm -r --cached custom_components/family_hub/__pycache__`, verify with `git ls-files | grep -c pyc` equals 0, make this its own commit, and add the CI guard (Phase 3) for tracked `*.pyc`, `*.bak*`, `*.orig`. Do not rewrite history; it is not needed. Also remove `card/*.bak_divfix` and make `.gitignore` cover `*.bak*`.
**Phase:** 1

### Pitfall 23: JS tests that cannot load the cards

**What goes wrong:** The cards are IIFE-wrapped ES modules calling `customElements.define` against HA's global custom elements, with no exports. jsdom smoke tests fail on `HTMLElement` shadow DOM features, `ha-*` elements, `hass.callWS`, and the translation loader.
**Prevention:** Prefer Playwright on the real Preview over jsdom for "does it load and render" (it also yields the before/after screenshots she needs); use jsdom only for pure helpers if the helper can be extracted. Provide a `hass` mock fixture (`language`, `localize`, `loadBackendTranslation`, `callWS`, `states`, `user`) once and reuse it. Assert no `console.error` and that the translation loader resolved.
**Phase:** 3

### Pitfall 24: Screenshot comparisons that flap

**What goes wrong:** Playwright screenshots differ run-to-run because of time-of-day, the "Right Now" bar, 60s polling, fonts and animations; "before/after" pictures for her show unrelated differences.
**Prevention:** Freeze time in the browser (Playwright clock), seed relative to a fixed "today" for screenshot runs, hide the clock, disable animations, fixed viewport equal to the tablet's, run in the same container image locally and in CI. Use screenshots for her review, not as pass/fail assertions at first.
**Phase:** 3

### Pitfall 25: CI that runs on forks' upstream or on every push with secrets

**What goes wrong:** A CI workflow needs a token (deploy-preview, Playwright against Preview) and leaks it to PRs from forks, or deploy-docs keeps pointing at upstream URLs. The existing `deploy-docs.yml` can start failing silently after the rename of the repo (base URL/org in `website/docusaurus.config.js`).
**Prevention:** Keep CI hermetic (no network to Preview/Home); `deploy-preview` is run by hand by the developer. Update Docusaurus `url`/`baseUrl`/`organizationName`/`projectName` for the fork in Phase 1 and check the docs workflow after the rename. Pin action versions.
**Phase:** 1 (docs config), 3

---

## Minor Pitfalls

### Pitfall 26: Repo hygiene renames break links
Renaming `\Screenshots/` to `screenshots/` (or deleting it) leaves README, `website/docs`, and docs images pointing at the old path. On Windows clones the backslash name is an invalid path. **Prevention:** `git mv` using a quoted path, grep for the old name in `README.md`, `DOCUMENTATION.md`, `website/`, and prefer deleting if `images/readme/` covers the images. **Phase:** 1

### Pitfall 27: Dedupe of `icon (1).png`, `icon.png`, `icon@2x.png`, `logo*.png`, `brand/`
HACS validation wants `brand/icon.png`; the integration also serves `icon.png` from the integration root via `ICON_URL` (`__init__.py`), so deleting the root `icon.png` silently removes the panel icon. **Prevention:** keep `icon.png` where `ICON_URL` is served, delete only `icon (1).png` after a checksum compare, and grep for each filename before removing. **Phase:** 1

### Pitfall 28: Empty `custom_components/family_hub/readme.md` removal vs HACS `render_readme`
`render_readme: true` in `hacs.json` renders the repo-root README; removing the empty integration-level `readme.md` is safe but verify HACS still shows the root README after a Home HACS refresh. **Phase:** 1

### Pitfall 29: Changelog sources keep disagreeing
Three changelogs (root, website, archive) and a dangling `CHANGELOG_ARCHIVE.md` link; `whats-new.md` for her adds a fourth. **Prevention:** website changelog as the only source for developer notes, `docs/family/whats-new.md` generated by hand per release in plain language, and the release script checks that they exist for the new version. **Phase:** 1 (decide), 4 (per release)

### Pitfall 30: Preview HA upgrade breaks the Preview mid-test
Automatic HA container image updates (watchtower, `latest`) change core underneath her. **Prevention:** pinned tag, upgrade by hand and announce. **Phase:** 2

### Pitfall 31: Time zone, language and units differ between Dev, Preview, and Home
The calendar card, reminders and translation selection all depend on them. **Prevention:** put `time_zone`, `language`, `unit_system`, `country` in the shared seed config copied from Home's values. **Phase:** 2

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Cloning Home's `config/` to make Preview | Preview looks like Home in minutes | Same `core.uuid`, real calendars/tokens/notify targets leak into Preview; defeats the safety promise | Never |
| Hand-editing `.storage/*` JSON for seed data | Fast first prototype | Overwritten on HA stop; breaks on HA storage schema change | Only while HA is stopped, pinned to one HA version, as a performance optimisation after the API-based seed exists |
| `continue-on-error: true` on hassfest/HACS | CI green immediately | Rules never enforced; the first real failure is invisible | Short, time-boxed (one phase), with a tracked issue |
| Global coverage gate (for example 80%) | Looks rigorous | Forces junk tests on 28k lines or the gate is switched off | Never; use per-module or no-regression gates |
| Reformatting the monoliths | Consistent style | Huge diff, lost blame, impossible upstream cherry-picks | Never for `__init__.py` and the calendar card in this milestone |
| Tests that import full `async_setup_entry` first | "Integration" feel | Brittle on HA internals, slow, lingering-timer failures | After engine and config-flow tests exist |
| Keeping the root copies "just in case" | Feels safe | Edits land in dead files again | Never after the Phase 1 triage |
| Starting a brand-new version scheme (for example `0.1.0`) | Fresh start | HACS sees a downgrade; no updates offered | Never; stay monotonic above 1.168.85 |
| Skipping tags/releases for Home | Less ceremony | No rollback; Home installs the default branch tip | Never for Home; fine for Preview |
| Preview on the developer's laptop | No extra hardware | Not always-on; she can't test when she wants | Only as a stopgap for the first day |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| HA Companion app | Adding Preview by replacing Home, or using the same HA account/server name | Add as a second server with a distinct name; non-admin Preview user; "PREVIEW" in name and theme |
| HA Companion push notifications | Letting auto-discovered `notify.mobile_app_*` in Preview reach her real phone | Preview-only notify allow-list; check in `deploy-preview`; device names prefixed "Preview" |
| mDNS / SSDP / Zeroconf | `network_mode: host` for Preview | Bridge network, explicit port, discovery components disabled |
| Lovelace resources | Assuming the integration's best-effort registration worked | Verify via `lovelace/resources` and served hash; add by WebSocket if missing |
| Local Calendar / Local To-do | Seeding with fixed dates | Seeds relative to now, through services, in Home's time zone |
| HA onboarding | Clicking through the wizard by hand and forgetting steps | Script via onboarding API; create admin (developer) and non-admin (her) users; record tokens in gitignored `.env` |
| HACS (Home) | Leaving the upstream repo as the tracked custom repository | Re-add the fork's repo, remove the upstream one, install from releases |
| HACS validation action | Running it on a fork with Issues disabled and no description/topics | Enable Issues, set description/topics first |
| hassfest | Treating the custom `fh_ui` translation category as normal | Spike the failure; decide a narrow exception or schema-valid move |
| Grocy (optional) | Pointing Preview at the real Grocy | Preview runs without Grocy or against a demo Grocy; never the real API key |
| GitHub issue template | Free-text requests with no context | Template with "where were you", screenshot, "what did you expect" in plain language |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Testing only on a phone, shipping to a low-power wall tablet | Calendar card janky or slow on first paint after the change | Test on the real tablet in Preview before sign-off; record load time as a UAT criterion | Any change that adds to the 1.7 MB calendar bundle |
| Adding more code to the single calendar-card file | Larger parse time, longer blank screen on the tablet | New logic in a separate file loaded on demand | Cumulative; noticeable around 2 MB |
| Per-start hashing of 14 card files (`_file_content_hash`) on a small Preview host | Slower HA start; noticeable on SD-card hosts | Cache by mtime/size (already noted in CONCERNS) | Small ARM boards |
| 60-second card polling plus a 5-minute backend poller on seeded data | Preview CPU/log noise; reminder bursts after a reset | Seed reminders carefully (Pitfall 2) | After a reset with many near-term events |
| Weekly `reset-preview` while she is testing | Data disappears mid-session | Fixed schedule published to her; reset during night | When scheduled automatically without notice |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Committing seed data with real family details or screenshots from Home to a public fork | Privacy leak of children's names, schedules, address | Pretend names; Preview-only screenshots; review `docs/family/` before each commit |
| `.env` or long-lived HA tokens not in `.gitignore` | Token leak gives control of Preview (and Home if reused) | Add `.env`, `*.env`, `secrets*`, `.storage/` to `.gitignore` in Phase 1; separate tokens per environment; secret scanning in CI |
| Exposing Preview to the internet with port-forwarding | Open HA instance with a weak password and fake data, still on the home network | Home Wi-Fi only or Tailscale; no port-forward |
| Reusing Home credentials/accounts on Preview | One compromise reaches both | Distinct users and passwords per environment |
| Self-updater available in Preview/Home | Anyone with admin can overwrite the integration (existing concern) | Do not use it; HACS releases only; document |
| Giving her an admin user | A tap in Settings can change real config | Non-admin user for her; admin only for the developer |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Preview looks identical to Home | She edits the wrong one, or trusts a test as real | "PREVIEW" in name, theme colour, and a card header |
| HA's technical chrome (sidebar, Repairs, Settings) visible | Confusion; fear of breaking something | Hide sidebar items for her user; kiosk-style dashboard |
| Change deployed with no "where to look" | She can't find it and says "nothing changed" | Each deploy message says "Open Chores, tap the star, you should see X" with a screenshot |
| Asking for opinions instead of tasks | Vague feedback | Task-based UAT (Pitfall 15) |
| Release to Home mid-day | Wall tablet breaks during morning routine | Release in the evening; tablet reload step; rollback ready |
| Jargon in `whats-new.md` | She skips it | Plain language, one screenshot, "where to find it" |

## "Looks Done But Isn't" Checklist

- [ ] **Duplicate cleanup:** often missing a read-through of root-only lines and root-only translation keys. Verify the triage notes exist and that CI rejects `*.js` outside `card/` and `panel/`.
- [ ] **Translation move:** key parity passes but not verified in the UI. Verify a Dev HA user set to `nl` and `pt-BR` shows translated labels after a full restart, with no `failed to load` console warning.
- [ ] **`.pyc` untracked:** the files remain in a second worktree or branch. Verify `git ls-files | grep -c '\.pyc$'` is 0 on `main` and on the fresh clone used by CI.
- [ ] **Fork identity:** `manifest.json` updated but Home's HACS still tracks upstream. Verify the HACS repository entry on Home and that a published release shows up as an update.
- [ ] **Versioning:** manifest, tag, `CHANGELOG.md`, website changelog all say the same number; checked by script.
- [ ] **Preview isolation:** it "has its own volume" but shares `core.uuid` or notify targets. Verify distinct `core.uuid`, distinct instance name, no `mobile_app` of a real family phone, no `media_player`, Preview unreachable from Home's allow-lists.
- [ ] **Seed data:** it loads once. Verify `reset-preview` twice in a row gives identical state, including after waiting past midnight, and that `family_hub_backups/` is cleared.
- [ ] **Her access:** works on the developer's phone. Verify on her own phone and the tablet, as her non-admin user, from the Wi-Fi she uses.
- [ ] **Card loads:** the Lovelace resources list contains all 14 `family_hub_*` URLs and the served hash equals the repo hash.
- [ ] **Cache busting:** build stamp visible and changed after deploy on her device without clearing the app cache by hand.
- [ ] **Test harness:** tests run in CI on the same Python/HA versions as locally; the unload of the config entry happens; a test fails when you break the code on purpose.
- [ ] **hassfest/HACS:** green on `main` and on PRs; no `continue-on-error`; manifest sorted; `hacs.json` HA minimum equals the pinned tested version.
- [ ] **Release to Home:** HA full backup taken, rollback tag identified, wall-tablet reload tested, `whats-new.md` entry written, her sign-off recorded with the build stamp.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Preview shares identity with Home | MEDIUM | Delete Preview server from Companion app; wipe Preview volume, re-onboard with a fresh `core.uuid`; verify Home's server entry in the app is intact |
| Notification to real phones | LOW | Stop Preview, remove the notify target, tell the family it was a test; add the allow-list check |
| Reset resurrects old data | LOW | Stop HA, delete `.storage`, `family_hub_backups/`, DB, ICS files; reseed |
| Card not found in Preview | LOW | Add resource through `lovelace/resources/create` or UI once; fix registration verification |
| Stale JS on her device | LOW | Reload / reset frontend cache; confirm build stamp |
| Deleted a root file that held needed content | LOW | `git revert` the deletion commit (or `git show <sha>:path`); port into `card/` |
| Wrong HACS source on Home | MEDIUM | Remove the upstream repo in HACS, add the fork, redownload latest release, restart; entities persist because `domain` is unchanged |
| Bad release on Home | MEDIUM | HACS redownload previous tag, restart; if settings were migrated, restore from the pre-release HA backup or `family_hub_backups/` |
| Wrong `domain`/identifier renamed | HIGH | Revert the rename; if config entry was recreated, rely on `family_hub_backups/` auto-restore for Stores and re-add dashboards |
| Secrets/family data committed | HIGH | Rotate tokens at once; purge with history rewrite on the fork (coordinate), replace screenshots |
| Test harness abandoned | MEDIUM | Reduce scope to pure-engine tests with a minimal conftest; re-introduce HA fixtures later |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 1 Preview shares identity with Home | 2 | Distinct `core.uuid`, name, port, theme; both servers listed separately in the Companion app |
| 2 Notifications/timers to real devices | 2, 4 | `deploy-preview` allow-list check passes; test reminder arrives only at a Preview-named device |
| 3 Reset vs backup-restore / write-on-stop | 2 | Seed, mutate, `reset-preview`, state equals seed; `family_hub_backups/` empty after reset |
| 4 Stale absolute-date seeds | 2, 4 | Run seed on two different dates; Today card populated both times |
| 5 Card not registered on fresh Preview | 2 | `lovelace/resources` lists 14 URLs; served hash equals repo hash |
| 6 Old JS visible, no way to tell | 2, 4 | Build stamp visible on her device after deploy |
| 7 Root duplicate deletion / upstream sync | 1, 3 | Triage notes; CI rejects stray `.js`/`.json`; `upstream` remote policy written |
| 8 Translation move | 1, 3 | Parity script green; Dev UI shows `nl` and `pt-BR` strings after restart |
| 9 Fork identity over-/under-reach | 1, 2 | `domain` unchanged; Home HACS tracks the fork |
| 10 Versioning / HACS detection | 1, 3, 4 | Release with tag equal to manifest appears as update in HACS on Preview-like instance; rollback rehearsed |
| 11 Preview not equal to Home | 2, 4 | `versions.env` equals Home's HA version; upgrade rehearsal on home-shaped fixture before each release |
| 12 Test harness bootstrap | 3 | Engine tests green in CI on pinned versions; deliberately broken code fails a test |
| 13 hassfest/HACS first-run failures | 3 (spike at end of 1) | Required checks green; no unexplained `continue-on-error` |
| 14 HA minimum version mismatch | 1, 3 | `hacs.json`, README, CI pin and Home version agree |
| 15 Non-technical UAT | 2, 4 | She completes three tasks unaided on the first session; recorded sign-off with build stamp |
| 16 Monolith edits without tests | 3, 4 | No Phase 4 change to a monolith without a covering test; diff size to monoliths is small |
| 17 Self-updater vs Dev mount | 2 | Self-updater not used; bind mount protected |
| 18 Stale files on deploy | 2 | Deploy output shows removed files gone and new hash |
| 19 Always-on host choice | 2 | Preview reachable at 7am Sunday without the developer |
| 20 Companion app set-up | 2 | Tested on a spare phone; Home server still present |
| 21 Family data in a public repo | 1, 2 | `.gitignore` has `.env`; secret scan in CI; docs screenshots audited |
| 22 `.pyc` untracking | 1, 3 | Zero tracked `.pyc` in fresh clone; CI guard |
| 23 JS tests can't load cards | 3 | Playwright smoke renders each card on Preview/Dev with no console errors |
| 24 Flapping screenshots | 3 | Two consecutive runs produce identical images |
| 25 CI/docs after rename | 1, 3 | Docs workflow green after rename; no secrets in CI |
| 26-28 Hygiene renames | 1 | Grep for old names returns nothing; HACS still shows README and icon |
| 29 Changelog drift | 1, 4 | Release script checks all sources |
| 30 Preview auto-upgrade | 2 | Image tag pinned |
| 31 Time zone/language/units drift | 2 | Config copied from Home values |

## Sources

- `.planning/PROJECT.md` and `.planning/codebase/CONCERNS.md` (provided context). `[repo]`
- Direct repository inspection on 2026-10-26: `custom_components/family_hub/{manifest.json,store.py,__init__.py,card/,panel/,translations/,strings.json}`, `hacs.json`, `.gitignore`, git history of `8f7172d`/`74bb966`, scripted key-parity and placeholder checks across all translation files, per-file root-versus-served line diffs. HIGH.
- Home Assistant contributor documentation on custom-integration translations (`translations/` per language, `en.json` required fallback, no `strings.json` for custom integrations, placeholder mismatch drops translations, no `[%key:...%]` references, hassfest string rules): https://contributors.home-assistant.io/core/integrations/translations/ HIGH
- HACS integration publishing requirements (single integration folder, `manifest.json` keys, `brand/icon.png`, releases preferred and default-branch fallback): https://www.hacs.xyz/docs/publish/integration/ MEDIUM (page does not cover the action checks)
- pytest-homeassistant-custom-component README and PyPI notes (`enable_custom_integrations` fixture; version tracks HA releases): https://pypi.org/project/pytest-homeassistant-custom-component/0.13.349/ MEDIUM (current pin not confirmed)
- Community report of HACS brands validation and a project that re-tagged after adding brand assets and sorting manifest keys for hassfest: https://git.supported.systems/warehack.ing/omni-pca/commits/tag/v2026.5.14 LOW
- Home Assistant general behaviour (Companion app multi-server and push relay, `.storage` write-on-stop, discovery over host networking, hassfest manifest ordering and services/translation checks, HACS fork defaults): `[HA knowledge]`, MEDIUM; items marked `[verify]` should be confirmed by a short spike before the roadmap depends on them.

---
*Pitfalls research for: forked Home Assistant custom integration with a family preview loop*
*Researched: 2026-10-26*
