---
phase: 01-clean-foundation
verified: 2026-10-27T00:00:00Z
status: human_needed
score: 52/53 must-haves verified
covered_files:
  - ".claude/CLAUDE.md"
  - ".github/workflows/validate.yml"
  - ".gitignore"
  - ".planning/phases/01-clean-foundation/01-01-PLAN.md"
  - ".planning/phases/01-clean-foundation/01-01-SUMMARY.md"
  - ".planning/phases/01-clean-foundation/01-02-PLAN.md"
  - ".planning/phases/01-clean-foundation/01-02-SUMMARY.md"
  - ".planning/phases/01-clean-foundation/01-03-PLAN.md"
  - ".planning/phases/01-clean-foundation/01-03-SUMMARY.md"
  - ".planning/phases/01-clean-foundation/01-04-PLAN.md"
  - ".planning/phases/01-clean-foundation/01-04-SUMMARY.md"
  - ".planning/phases/01-clean-foundation/01-05-PLAN.md"
  - ".planning/phases/01-clean-foundation/01-05-SUMMARY.md"
  - ".planning/phases/01-clean-foundation/01-06-PLAN.md"
  - ".planning/phases/01-clean-foundation/01-06-SUMMARY.md"
  - ".planning/phases/01-clean-foundation/01-07-PLAN.md"
  - ".planning/phases/01-clean-foundation/01-07-SUMMARY.md"
  - "CHANGELOG.md"
  - "README.md"
  - "custom_components/family_hub/__init__.py"
  - "custom_components/family_hub/config_flow.py"
  - "custom_components/family_hub/manifest.json"
  - "custom_components/family_hub/translations/en.json"
  - "custom_components/family_hub/translations/it.json"
  - "custom_components/family_hub/translations/nl.json"
  - "custom_components/family_hub/translations/pl.json"
  - "custom_components/family_hub/translations/pt-BR.json"
  - "custom_components/family_hub/translations/pt.json"
  - "hacs.json"
  - "versions.env"
  - "website/docs/installation.md"
  - "website/docs/intro.md"
  - "website/docs/license.md"
  - "website/docusaurus.config.js"
covered_digest: "v3:sha256:c53bf899a6da64279d263bd6683cd5600b24ef0841bcdfb9820979e1c94e7ac1"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Confirm the FOUND-07 ordering rule (01-04 truth tagged verification: backstop): every future release version is strictly greater than the previous one and no published number is reused"
    expected: "PROJECT.md 'Fork versioning' row states the rule (verifier observed the text); you accept that enforcement is deferred to the Phase 4 REL-01 tag check"
    why_human: "Backstop truth is non-inferable: no held-out or property test exists, so the verifier abstains (insufficient_spec) even though the recorded text is present"
  - test: "Resolve prohibition FOUND-04 (test tier): MUST NOT commit HA runtime state, integration backups or env files"
    expected: "Accept the verifier evidence: 0 tracked .storage/, family_hub_backups/ or .env paths; git check-ignore confirms all three are ignored"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed, flagged unverified). CI guard arrives in Phase 3 (CI-04)"
  - test: "Resolve prohibition FOUND-05 (test tier): MUST NOT delete served brand art or make any runtime change"
    expected: "Accept: icon.png and brand/* tracked and unchanged; git diff bc7e90c..HEAD on card/, panel/, *.py, services.yaml, de/en/es/fr translations, icon, brand shows only the .bak_divfix deletion"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed)"
  - test: "Resolve prohibition FOUND-01 (test tier): MUST NOT change served card/panel JS except via a ported-hunk port commit"
    expected: "Accept: 01-TRIAGE.md has 14 discarded rows and 'Ported hunks: none'; served card/*.js and panel/*.js are byte-identical to bc7e90c; no Python or services.yaml change"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed)"
  - test: "Resolve prohibition FOUND-06 values (test tier): MUST NOT remove the Bordello Labs notice, edit LICENSE, or present the fork as original work"
    expected: "Accept: LICENSE unchanged vs bc7e90c; README line 153 credit 'Based on [JVarhol/HA-Family-Hub]... licensed GPLv3.'; site footer keeps 'Bordello Labs' plus the upstream credit"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed)"
  - test: "Resolve prohibition FOUND-06 safety (test tier): MUST NOT change domain, name, service names, websocket prefixes, card tags, storage keys or static URL paths"
    expected: "Accept: manifest domain family_hub / name Family Hub; all *.py (incl. const.py), services.yaml and served JS unchanged vs bc7e90c"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed)"
  - test: "Resolve prohibition FOUND-09 transparency (test tier): workflow carries no error suppression"
    expected: "Accept: validate.yml has no continue-on-error or '|| true'; hosted run 40422777272 shows both jobs red"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed)"
  - test: "Resolve prohibition FOUND-08 (test tier): MUST NOT set hacs.json minimum above what the code needs"
    expected: "Accept: hacs.json homeassistant is 2024.12.0 (not 2026.10.4); config_flow.py builds FamilyHubOptionsFlow() with no argument, which needs the 2024.12 OptionsFlow.config_entry property"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed)"
  - test: "Resolve prohibition FOUND-07 (test tier): MUST NOT set a manifest version <= 1.168.85 or reuse a published number"
    expected: "Accept: manifest version 2.0.0 compares greater than (1,168,85) numerically; 2.0.0 has never been published by the fork"
    why_human: "Test-tier prohibition with no wired enforcement check (fail-closed); release-tag enforcement is Phase 4 REL-01"
  - test: "Resolve prohibition FOUND-02 / FOUND-03 (test tier): MUST NOT alter any translation string or key while moving or deleting files, and MUST NOT port the 9 orphan keys"
    expected: "Accept: move commit 3c9a703 is 5 exact renames (0 insertions, 0 deletions); de/en/es/fr in translations/ unchanged vs bc7e90c; all 9 languages have 2,139 keys with symmetric difference 0; the 9 orphan leaf names match 0 files under custom_components/"
    why_human: "Test-tier prohibitions with no wired enforcement check (fail-closed)"
  - test: "Resolve prohibition FOUND-09 (judgment tier): MUST NOT soften, reword away or omit any validation failure"
    expected: "Non-authoritative verifier judgment: holds. The hosted section's failure lines match the live check-run annotations line for line (MANIFEST, fh_ui, two grocy_url URL lines, CONFIG_SCHEMA warning; HACS license, issues, topics, categories warning, '3/10 checks failed'). Issues, topics and LICENSE were not changed before the run"
    why_human: "Judgment-tier prohibition always needs explicit human resolution"
---

# Phase 1: Clean Foundation Verification Report

**Phase Goal:** As a developer, I want to work in a clean fork with one served copy of every file, so that each edit lands where Home Assistant loads it.
**Verified:** 2026-10-27
**Status:** human_needed
**Re-verification:** No, this is the first verification.

All 5 roadmap success criteria and 52 of 53 plan truths were checked against the repository at HEAD `06154cd` and against the live GitHub API. Nothing failed. The status is `human_needed` because of the fail-closed prohibition policy and one backstop truth. The code work is complete.

## User Flow Coverage (MVP mode)

The user story format check passed (`user-story.validate` returned `valid: true`).

| Step | Expected | Evidence in codebase | Status |
|------|----------|----------------------|--------|
| Developer opens the integration folder to edit a card | Exactly one copy of each card and panel exists | Only `card/` (12 files) and `panel/` (2 files) hold `.js` under `custom_components/family_hub/`, on disk and in the index. Commit `b7353c6` deleted the 14 root duplicates | VERIFIED |
| Developer edits that copy | The edited file is the one HA serves | All 15 `f"{integration_dir}/..."` paths in `__init__.py` (lines 12504-12550) are tracked. `unregistered js []` | VERIFIED |
| Developer edits a translation | One file per language, in the folder HA reads | `translations/` holds 9 languages. The only root `.json` is `manifest.json` | VERIFIED |
| Developer commits | No build junk or local state ends up in git | 0 tracked `.pyc`/`__pycache__`. `.gitignore` covers `.env`, `*.bak*`, `family_hub_backups/`, `.storage/` and `dev/.ha-*` (checked with `git check-ignore`) | VERIFIED |
| Outcome: each edit lands where HA loads it | Served-path contract holds | `reg 15`, `missing []`, `unregistered js []` (verifier's own script) | VERIFIED |

## Goal Achievement

### Roadmap Success Criteria

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | Cards and panels exist only in `card/`/`panel/` and translations only in `translations/`. No root `.js`, `.bak_divfix`, root de/en/es/fr.json or `strings.json` remains. Root-only content was triaged in `01-TRIAGE.md`, and the 9 orphan keys were reviewed and not ported | VERIFIED | `git ls-files` at the integration root shows only `.py`, `services.yaml`, `icon.png` and `manifest.json`. 0 tracked names contain `.bak`. `01-TRIAGE.md` has 14 rows marked discarded, the `.bak_divfix` line, the 9 orphan keys verbatim and the strings.json diff (566 keys, 2 only in strings.json). The 9 orphan leaf names match 0 files under `custom_components/` |
| SC2 | it/nl/pl/pt/pt-BR sit in `translations/`, each with the same 2,139 keys as en.json, and `fh_ui` is kept | VERIFIED | Verifier's flatten script: all 9 files have 2139 keys, symmetric difference 0, and `fh_ui` present. pt and pt-BR are separate files with md5 `2c33d85a…` (identical). Commit `3c9a703` is 5 renames with 0 lines changed. The hosted hassfest still reports the `fh_ui` objection, so the category is kept |
| SC3 | No tracked `.pyc`, no `\Screenshots/`, no duplicate icons, no empty readme.md. `.gitignore` covers `.env`, `*.bak*`, `family_hub_backups/`, `.storage/` | VERIFIED | 0 `.pyc` (commit `d61341f`, 49 deletions). 0 `\Screenshots` paths. The four root icon/logo copies are gone, and `icon.png` (served) plus `brand/*` are kept. `readme.md` is gone. `.gitignore` sha256 `a2ca450d…` matches the plan. `git check-ignore` matches all four patterns and does not ignore `versions.env` |
| SC4 | Manifest, codeowners, README badges, HACS links and the docs site point at `Future-Bridge-AI/HA-Family-Hub`. Upstream credit and GPLv3 are kept. Manifest carries the next fork version. domain, services, ws prefixes and card tags are unchanged | VERIFIED | manifest: codeowners `@Future-Bridge-AI`, documentation and issue_tracker point at the fork, version `2.0.0` (developer's D-19 choice; strictly above 1.168.85). In README, docusaurus.config.js and the 3 docs pages, upstream is named only in the README line 153 credit and the footer credit. LICENSE is unchanged. All `*.py`, `services.yaml` and served JS are unchanged vs `bc7e90c` |
| SC5 | One pinned HA version is recorded. The hacs.json minimum matches what the code needs. The first hassfest/HACS failure list is recorded | VERIFIED | `versions.env` HA_VERSION=2026.10.4 and HA_MIN_VERSION=2024.12.0, which equals `hacs.json`. `config_flow.py:768` returns `FamilyHubOptionsFlow()` with no argument and uses `self.config_entry` (needs 2024.12). `__init__.py` imports `StaticPathConfig` and calendar `DATA_COMPONENT`. `01-VALIDATION-BASELINE.md` records HF-01..04, HF-W01, HACS-01..03 and HACS-W01. Hosted run 40422777272 was confirmed independently through the GitHub API: completed, both validator steps concluded `failure`, head `bd8de7a`, and the annotations match the recorded lines. No non-planning file changed between `bd8de7a` and HEAD |

### Plan Truths (merged, beyond the roadmap wording)

| Plan | Truths | Status | Notes |
|------|--------|--------|-------|
| 01-01 | 7 | 7 VERIFIED | Commit shapes: `d61341f` has 49 deletions only. `ddc3442` has 20 deletions and 1 modification (.gitignore), with no additions or renames. Local hassfest outputs (`$HOME/.cache/fh-hassfest/hassfest-01-01.txt`, `-01-07.txt`, `-01-05.txt`) all print `Integrations: 1` |
| 01-02 | 4 | 4 VERIFIED | Served-path contract holds. 14 rows say discarded and there is no port commit. `b7353c6` has 14 deletions only. All 14 served JS files pass `node --check` |
| 01-03 | 8 | 8 VERIFIED | Manifest key order is unchanged. `validate.yml` has jobs `hacs` and `hassfest`, triggers on push, pull_request and workflow_dispatch, sets `permissions: {}` with contents: read on hassfest, and has no suppression, secrets or concurrency. The CHANGELOG_ARCHIVE link now points at `website/docs/changelog-archive.md` (exists). The historical changelogs are unchanged. Owner spelling is case-exact |
| 01-04 | 9 | 8 VERIFIED, 1 insufficient_spec | versions.env keys and values are exact. hacs.json key order is name, render_readme, homeassistant. No `2024.1` minimum wording remains in PROJECT.md, CLAUDE.md or STACK.md. The version-scheme row in PROJECT.md says Decided. The backstop truth (future-version ordering rule) has its text present, but the verifier abstains per policy, so it goes to human verification |
| 01-05 | 9 | 9 VERIFIED | The baseline has separate predicted, hosted and Differences sections. Every section has rows. IDs are stable. The manual steps are listed. The sweep table is present. The "Home HA version" truth is met by PROJECT.md line 96, which records that there is no Home install yet and that any Home must meet 2024.12.0. This is a documented deviation and still answers the question the truth asks. The hosted run is confirmed live |
| 01-06 | 4 | 4 VERIFIED | 9 languages with 2,139 keys each. pt and pt-BR are separate and identical. de/en/es/fr are unchanged vs `bc7e90c`. 5 exact renames |
| 01-07 | 7 | 7 VERIFIED | `5dd2cae` deletes exactly root de/en/es/fr.json and strings.json. `0ca31a8` deletes only `.bak_divfix`. The move commit `3c9a703` is an ancestor of `5dd2cae`. Hassfest output after the deletions has no strings.json error and still has the fh_ui error |

**Score:** 52/53 truths verified (0 present but behavior-unverified; 1 insufficient_spec backstop routed to human).

### Prohibitions (must-NOT checks)

Each test-tier item fails closed by policy because no wired enforcement check exists yet; the Phase 3 CI guards are meant to provide one. The verifier's own read-only checks found that every item holds. That finding is a non-authoritative judgment and is listed under Human Verification.

| Req | Tier | Statement (short) | Verifier judgment | Disposition |
|-----|------|-------------------|-------------------|-------------|
| FOUND-04 | test | No runtime state, backups or env files committed | holds (0 tracked, all ignored) | flagged unverified |
| FOUND-05 | test | No served brand art removed, no runtime change | holds | flagged unverified |
| FOUND-01 | test | Served JS only changed by port commits | holds (byte-identical, no ports) | flagged unverified |
| FOUND-06 | test | Credit, Bordello Labs notice and LICENSE kept | holds | flagged unverified |
| FOUND-06 | test | Domain, services, ws prefixes, tags, storage keys and URLs unchanged | holds | flagged unverified |
| FOUND-09 | test | No error suppression in workflow | holds | flagged unverified |
| FOUND-08 | test | hacs.json minimum not above code need | holds (2024.12.0) | flagged unverified |
| FOUND-07 | test | Version > 1.168.85, not reused | holds (2.0.0) | flagged unverified |
| FOUND-02 | test | Move alters no string or key | holds (R100 renames) | flagged unverified |
| FOUND-03 | test | No translation altered, orphans not ported | holds | flagged unverified |
| FOUND-09 | judgment | Failures not softened or omitted | holds (matches live annotations) | human resolution required |

### Required Artifacts

`verify.artifacts` reports all_passed for all 7 plans (16 of 16 artifacts).

| Artifact | Status | Details |
|----------|--------|---------|
| `.planning/phases/01-clean-foundation/01-TRIAGE.md` | VERIFIED | Has every required section. Every figure checked again matches the tree |
| `.gitignore` | VERIFIED | 11 lines, sha256 matches the plan |
| `.github/workflows/validate.yml` | VERIFIED | Ran on GitHub (run 40422777272) |
| `custom_components/family_hub/manifest.json` | VERIFIED | Fork identity, version 2.0.0 |
| `README.md` | VERIFIED | Fork links and upstream credit |
| `versions.env` | VERIFIED | 4 KEY=value lines, not ignored |
| `hacs.json` | VERIFIED | `"homeassistant": "2024.12.0"` |
| `.planning/phases/01-clean-foundation/01-VALIDATION-BASELINE.md` | VERIFIED | Has the hosted section with a run URL and one line per job |
| `custom_components/family_hub/translations/{it,nl,pl,pt,pt-BR}.json` | VERIFIED | Each has `fh_ui` and 2,139 keys |

### Key Link Verification

`verify.key-links` reports all_verified for all 7 plans (15 of 15 links). The verifier also checked these links by hand:

| From | To | Via | Status |
|------|----|-----|--------|
| `__init__.py` async_setup_entry | `card/`, `panel/`, `icon.png` | 15 StaticPathConfig paths | WIRED, all tracked |
| cards (`loadBackendTranslation`) | `translations/<lang>.json` | HA backend translation loader | WIRED, 9 languages present |
| `validate.yml` | `01-VALIDATION-BASELINE.md` | hosted run fills the Hosted section | WIRED, run URL confirmed live |
| `versions.env` HA_MIN_VERSION | `hacs.json` homeassistant | mirrored value | WIRED, both 2024.12.0 |

### Data-Flow Trace (Level 4)

Not applicable. The phase changes repository hygiene, metadata and config, and renders no dynamic data.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Served JS still parses | `node --check` on 14 card/panel files | 0 failures | PASS |
| Translation parity | flatten script over `translations/*.json` | 9 x 2139, sym diff 0 | PASS |
| Hosted validation executed | GitHub API run and jobs for run 40422777272 | completed; validator steps failure/failure | PASS |
| Ignore rules | `git check-ignore --no-index` on sample paths | 5 ignored; `versions.env` not ignored | PASS |
| Version strictly above upstream | tuple compare of manifest version | `(2,0,0) > (1,168,85)` is True | PASS |

The integration was not imported or compiled, as the orchestrator instructed, so no `.pyc` was regenerated.

### Probe Execution

None. No `scripts/*/tests/probe-*.sh` exists and no plan declares one.

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
|-------------|-------------|--------|----------|
| FOUND-01 | 01-02, 01-07 | SATISFIED | SC1. Root JS and `.bak_divfix` were removed after triage |
| FOUND-02 | 01-06 | SATISFIED | SC2 |
| FOUND-03 | 01-07 | SATISFIED | SC1 and SC2. Root de/en/es/fr and strings.json are gone, and `fh_ui` is kept |
| FOUND-04 | 01-01 | SATISFIED | SC3 |
| FOUND-05 | 01-01 | SATISFIED | SC3. No functional reference to `\Screenshots` remains; only prose audit notes in `docs/onboarding-findings.md` mention it |
| FOUND-06 | 01-03 | SATISFIED | SC4 |
| FOUND-07 | 01-04 | SATISFIED | 2.0.0 and the scheme are recorded in the PROJECT.md Key Decisions row |
| FOUND-08 | 01-04 | SATISFIED | SC5. The "what is tested" part relies on the pin; there is no test suite until Phase 3 |
| FOUND-09 | 01-03, 01-05 | SATISFIED | Hosted run executed and recorded |

All 9 IDs are claimed by plans. REQUIREMENTS.md maps no other ID to Phase 1, so nothing is orphaned.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (all phase-modified files) | - | TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER | none found | - |
| `.planning/ROADMAP.md` | Phase 1 plan list | Says "then manifest 1.169.0", but the shipped version is 2.0.0 (developer's D-19 choice) | Info | Stale wording only. SC4 is met |
| `docs/onboarding-findings.md` | 90, 124, 166 | Prose mentions of `\Screenshots/` and upstream links | Info | Historical audit note, not a link or reference to a file |
| `card/family-week-calendar-card.js` | 18080 | Comment mentions `admin_jvarhol_com` | Info | Served JS must stay unchanged in Phase 1. Not a link |

### Human Verification Required

1. **FOUND-07 ordering rule (backstop truth).** Read the PROJECT.md "Fork versioning" row. Expected: it states that versions are strictly increasing and never reused, and you accept that enforcement is deferred to Phase 4 REL-01. Why human: the truth is tagged backstop and non-inferable, so the verifier abstains.
2. **Ten test-tier prohibitions (FOUND-01 through FOUND-09).** Review the verifier evidence in the Prohibitions table and the frontmatter, then accept or reject each one. Expected: every item holds, as the verifier observed. Why human: no wired enforcement check exists, so policy fails closed; the CI guards arrive in Phase 3.
3. **FOUND-09 judgment-tier prohibition.** Compare the Hosted section of `01-VALIDATION-BASELINE.md` with the run page https://github.com/Future-Bridge-AI/HA-Family-Hub/actions/runs/40422777272. Expected: no failure was softened or omitted. The verifier found that the lines match the live annotations. Why human: judgment-tier items always need explicit resolution.

### Gaps Summary

There are no gaps. Every roadmap success criterion and requirement is met by evidence from the codebase and the GitHub API, not by SUMMARY claims. Two deviations are documented and acceptable:

- The manifest version is 2.0.0 rather than the planned default 1.169.0. The developer chose it at the D-19 checkpoint, and it is strictly above 1.168.85.
- PROJECT.md says "Home HA version: none yet" because no Home install exists.

Status is `human_needed` only because the prohibition policy fails closed and one backstop truth needs sign-off.

---

_Verified: 2026-10-27_
_Verifier: Claude (gsd-verifier)_
