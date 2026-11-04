# Phase 1: Clean Foundation - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning
**Mode:** `--auto` (recommended options auto-selected; see `01-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

Make the fork safe to edit: every card/panel exists once (in served `card/` / `panel/`), every
translation exists once (in `translations/`, all nine advertised languages loaded by HA), no compiled
Python or junk files are tracked, the fork carries its own identity and version scheme, the real
minimum HA version and one pinned HA version are recorded, and the first hassfest/HACS validation
failure list is written down for Phase 3.

Requirements: FOUND-01 … FOUND-09. Invisible to the family — no runtime behaviour, domain, service,
websocket or card-tag changes. Not in scope: Dev/Preview environments (Phase 2), tests and making
CI green (Phase 3), any feature work.

</domain>

<decisions>
## Implementation Decisions

### Root-level duplicate cards (FOUND-01)
- **D-01:** Triage each root-level `.js` against its served copy in `card/`/`panel/` before deleting. Default outcome is **delete the root copy without porting**: the served copies are the newer, live code (e.g. calendar 31k vs 23.5k lines), and root edits (including upstream commit `8f7172d`) never ran. Port a root-only hunk only if it is a clearly self-contained fix that is absent from the served copy; anything ambiguous is recorded, not ported.
- **D-02:** Record the triage outcome per file (kept / ported hunk / discarded, one line each) in a phase artifact `01-TRIAGE.md`, so the deletion is auditable later.
- **D-03:** Delete `card/family-week-calendar-card.js.bak_divfix` (≈1.2 MB). It is the only consumer of the 9 "orphan" translation keys (verified: `chore_due_label`, `small_screen_mode_hint`, `goals_in_chores_*` appear only there), so it is debris, not unfinished served work.
- **D-04:** Deletions go in their own commit(s), separate from any ported hunk, so a port can be reviewed and reverted independently.

### Translations (FOUND-02, FOUND-03)
- **D-05:** `git mv` `it`, `nl`, `pl`, `pt`, `pt-BR` from the integration root into `translations/` unchanged (key parity with `translations/en.json` already verified: 2,139 keys each, 0 missing, 0 extra).
- **D-06:** **Do not port** the 9 orphan keys from root `de`/`es`: no served code references them (only the `.bak_divfix` file does). Note them in `01-TRIAGE.md` in case upstream later ships the feature they belonged to.
- **D-07:** Delete the truncated root `de.json`, `en.json`, `es.json`, `fr.json` after a key diff against their `translations/` counterparts confirms nothing served is lost; record the diff summary in `01-TRIAGE.md`.
- **D-08:** Delete `strings.json` — custom integrations do not read it and it has diverged from `translations/en.json`.
- **D-09:** Preserve the non-standard `fh_ui` top-level category exactly as is (cards load it via `loadBackendTranslation("fh_ui", …)`). Any hassfest objection to it is recorded for Phase 3, not fixed here.

### Untracking and hygiene (FOUND-04, FOUND-05)
- **D-10:** `git rm -r --cached` all `custom_components/family_hub/__pycache__/` in its own commit (49 files). `.gitignore` already covers them; add `.env`, `*.bak*`, `family_hub_backups/`, `.storage/` (and `dev/.ha-*` style local HA volumes for Phase 2).
- **D-11:** Remove the `\Screenshots/` directory (15 tracked files, name begins with a literal backslash) rather than renaming it: `images/readme/` already holds the README/site screenshots and no file references `\Screenshots/` (the README "Screenshots" anchor points at its own `#a-look-around` section). If any image there has no equivalent in `images/readme/`, list it in `01-TRIAGE.md` before deleting.
- **D-12:** Icons — keep root `custom_components/family_hub/icon.png` (served: `ICON_URL` → `{integration_dir}/icon.png`, `__init__.py` ~12550) and the `brand/` folder (HACS/HA brand assets). Delete the byte-identical, unserved root duplicates `icon (1).png`, `icon@2x.png`, `logo.png`, `logo@2x.png` (md5 matches `brand/` copies).
- **D-13:** Delete the empty `custom_components/family_hub/readme.md` (1 byte); HACS renders the repo-root `README.md` (`render_readme: true`).

### Fork identity (FOUND-06)
- **D-14:** Codeowner becomes `@Future-Bridge-AI` (authenticated GitHub login); `documentation` → `https://github.com/Future-Bridge-AI/HA-Family-Hub`, `issue_tracker` → `…/issues`. — **Reversibility:** reversible.
- **D-15:** README badges, HACS one-click links and documentation links point at `Future-Bridge-AI/HA-Family-Hub`; docs site config (`website/docusaurus.config.js`: `url`, `organizationName`, `editUrl`, navbar/footer links, issues/releases links) points at the fork and `https://future-bridge-ai.github.io/HA-Family-Hub/`.
- **D-16:** Keep visible upstream credit: a short "Based on [JVarhol/HA-Family-Hub](…) by its original author, licensed GPLv3" line in README (and site footer if a credit line fits). `LICENSE` unchanged.
- **D-17:** Do NOT change `domain` (`family_hub`), integration `name`, service names, `family_hub/...` websocket prefixes, card element tags, storage keys or static URL paths — renaming any of these orphans saved dashboards/automations. — **Reversibility:** one-way — renaming after release breaks every saved dashboard, automation and stored data key.
- **D-18:** No ongoing upstream sync in this milestone. Record (in `01-TRIAGE.md` or a short note in `CONTRIBUTING`/README dev section) that any future upstream pull must map root-file edits onto `card/`/`panel/`/`translations/`.

### Versioning and HA versions (FOUND-07, FOUND-08)
- **D-19:** Continue upstream numbering, strictly monotonic: next fork version **1.169.0** set in `manifest.json` (fork-identity release). Git tags will be `vX.Y.Z` equal to `manifest.json`. Record the scheme in PROJECT.md Key Decisions. — **Reversibility:** one-way — once Home installs a fork release via HACS, a lower or reset number looks like a downgrade and no update is offered.
- **D-20:** Pinned HA version for Dev, Preview and tests: **2026.10.4** (the version `pytest-homeassistant-custom-component` 0.13.375 pins; requires Python 3.14). Record it once in a single `versions.env` (or equivalent) at repo root that Phase 2/3 tooling reads.
- **D-21:** `hacs.json` `homeassistant` minimum is set to the **lowest version the code actually needs**, not the pinned test version: verify when `StaticPathConfig` / `hass.http.async_register_static_paths` (and any other newest API used, e.g. calendar `DATA_COMPONENT`) became available and set the minimum to that release (expected ~2024.7+). Rationale: raising it to 2026.10.4 could block the family's Home HA from updating if it runs an older version. Update PROJECT.md's "HA >= 2024.1" constraint to match.

### Validation baseline (FOUND-09)
- **D-22:** Add a GitHub Actions workflow (`validate.yml`: `hacs/action@main` with `category: integration`, `home-assistant/actions/hassfest@master`, plus `workflow_dispatch`) in this phase, **non-blocking** (not a required check), run it once after the identity changes, and record the full failure list in `01-VALIDATION-BASELINE.md`. Fixing failures is Phase 3 work; do not add `continue-on-error` blankets.
- **D-23:** Repo-settings items HACS checks that can't be fixed in code (Issues enabled on the fork, repository description, topics) are listed in `01-VALIDATION-BASELINE.md` as manual steps for the developer.

### Commit structure
- **D-24:** One logical change per commit (untrack pyc; delete root JS; move translations; delete root translations + strings.json; hygiene deletions; identity; version + hacs.json; validate workflow), so each is independently revertible.

### Claude's Discretion
- Exact wording of the upstream credit line and of `01-TRIAGE.md` / `01-VALIDATION-BASELINE.md`.
- How to verify the minimum-HA API dates (HA release notes / source tags).
- Whether `versions.env` is a plain env file or another single-source format, as long as Phase 2/3 can read it.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project scope and decisions
- `.planning/PROJECT.md` — constraints (served paths, GPLv3, locality), Key Decisions to update (version scheme, min HA)
- `.planning/REQUIREMENTS.md` — FOUND-01 … FOUND-09
- `.planning/ROADMAP.md` — Phase 1 success criteria
- `docs/onboarding-findings.md` — original brief; "Problems found" items 1–7 and "Phase 1: Clean foundation"

### Research
- `.planning/research/SUMMARY.md` — Phase 1 deliverables, minimum-HA conflict, hassfest/HACS expectations
- `.planning/research/PITFALLS.md` — root-duplicate, translation, versioning, HACS/hassfest pitfalls
- `.planning/research/STACK.md` — pinned HA 2026.10.4, Python 3.14, CI action versions

### Codebase map
- `.planning/codebase/STRUCTURE.md` — where served vs duplicate files live
- `.planning/codebase/CONCERNS.md` — committed pyc, duplicates, `\Screenshots`, version mismatch, missing `CHANGELOG_ARCHIVE.md`
- `.planning/codebase/CONVENTIONS.md` — naming and "do not add `.bak_*`"

### Files touched
- `custom_components/family_hub/manifest.json`, `hacs.json`, `README.md`, `website/docusaurus.config.js`, `.gitignore`
- `custom_components/family_hub/__init__.py` ~12540–12610 — static path + icon registration (read-only reference: confirms served paths)
- `custom_components/family_hub/const.py` ~942–971, ~2277–2318 — served URL constants (read-only reference)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `custom_components/family_hub/brand/` — already holds icon/logo assets HACS and HA 2026.3+ use; no new brand work needed.
- `images/readme/` — the screenshots README and the docs site actually use.

### Established Patterns
- Only `card/` and `panel/` JS are registered as static paths (`StaticPathConfig` list around `__init__.py:12553`); root `.js` files are never served.
- HA loads only `translations/*.json`; cards fetch the `fh_ui` category through `loadBackendTranslation`.
- `ICON_URL = "/family_hub_static/icon.png"` serves the root `icon.png` — the one root image that must stay.

### Integration Points
- `manifest.json` / `hacs.json` / README / docs config are the only identity surfaces; no Python or JS references the upstream repo URL at runtime (verify with a grep for `JVarhol` outside docs during planning).
- `.github/workflows/` currently has only `deploy-docs.yml`; `validate.yml` is new and must not interfere with it.

</code_context>

<specifics>
## Specific Ideas

- Codeowner handle: `@Future-Bridge-AI`.
- Next version: `1.169.0`.
- Docs URL: `https://future-bridge-ai.github.io/HA-Family-Hub/`.
- The upstream `CHANGELOG.md` references a missing `CHANGELOG_ARCHIVE.md` — fix or remove the dangling link while touching README/CHANGELOG links (small, in scope as link hygiene).

</specifics>

<deferred>
## Deferred Ideas

- Fixing hassfest/HACS failures and making validation a required check — Phase 3 (CI-03).
- CI guards against stray root `.js`/`.pyc`/`*.bak*` and translation key drift — Phase 3 (CI-04).
- Moving `fh_ui` to a schema-valid location — decide in Phase 3 based on hassfest output.
- Bumping `deploy-docs.yml` off Node 20 — low priority, Phase 3 CI work.
- Reconciling `CHANGELOG.md` (stops at v1.135.4) with the manifest version history — Phase 4 release work (REL-01/LOOP-04).

</deferred>

---

*Phase: 01-clean-foundation*
*Context gathered: 2026-10-26*
