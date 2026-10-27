---
phase: "01"
slug: "clean-foundation"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-27"
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| working copy → git history | Anything committed is published to the public fork and every clone | Repo files; must never include HA state or family data (medium) |
| PyPI / GitHub → local harness | Third-party code is downloaded into a scratch venv outside the repo (`$HOME/.cache/fh-hassfest`) | Pinned Python packages (high) |
| git tree → HA loader on Home | Whatever is tracked is what HACS installs and what HA serves and loads as translations | Served card/panel JS, translations (high) |
| repo metadata → users/HACS | Links in manifest, README and docs send users and bug reports somewhere | Public URLs (medium) |
| GitHub Actions runner → repo | Third-party actions run with the workflow's GITHUB_TOKEN | Token scope (medium) |
| hacs.json / release version → Home's HACS | HACS decides from these whether it may install and whether an update is offered | Version metadata (high) |
| GitHub public API → planning docs | Run metadata and log lines from GitHub are copied into the repo | Public validator output (low) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Information disclosure | .gitignore / HA state | medium | mitigate | `.gitignore` lines 7, 9–11 ignore `.env`, `family_hub_backups/`, `.storage/`, `dev/.ha-*` (verified with `git check-ignore -v`) | closed |
| T-01-02 | Tampering | `\Screenshots/` deletion | medium | mitigate | Literal pathspec deletion; `git ls-files ':(literal)\Screenshots'` returns 0 files | closed |
| T-01-03 | Denial of service | served `icon.png` / `brand/` | low | mitigate | `git diff --quiet bc7e90c HEAD -- icon.png brand` passes (unchanged) | closed |
| T-01-04 | Tampering | repo tree during validation | low | mitigate | Harness lives under `$HOME/.cache/fh-hassfest`; `git status --porcelain` shows no harness files | closed |
| T-01-05 | Denial of service | served card/panel paths | high | mitigate | Every `f"{integration_dir}/…"` static path in `__init__.py` resolves to a tracked file | closed |
| T-01-06 | Repudiation | file deletions (01-02) | low | mitigate | Deletion-only commit `chore(01-02): delete stale root card and panel duplicates`, backed by 01-TRIAGE.md rows | closed |
| T-01-07 | Tampering | translation move | medium | mitigate | All nine `translations/*.json` files hold 2,139 leaf keys (parity re-checked) | closed |
| T-01-08 | Spoofing | identity links | medium | mitigate | `manifest.json` codeowner, documentation and issue_tracker point at `Future-Bridge-AI/HA-Family-Hub` | closed |
| T-01-09 | Elevation of privilege | validate.yml GITHUB_TOKEN | medium | mitigate | `permissions: {}` at workflow level; only the hassfest job has `contents: read` | closed |
| T-01-10 | Tampering | floating action refs | medium | accept | See accepted risk AR-01 | closed |
| T-01-11 | Elevation of privilege | PR-target trigger / secrets | high | mitigate | Triggers are exactly push, pull_request, workflow_dispatch; no `_target` and no `secrets.` in validate.yml | closed |
| T-01-12 | Repudiation | upstream attribution / GPLv3 | medium | mitigate | `LICENSE` unchanged against bc7e90c; README keeps the JVarhol credit line and Bordello Labs notice | closed |
| T-01-13 | Denial of service | hacs.json minimum | high | mitigate | `hacs.json` `homeassistant` is exactly `2024.12.0` | closed |
| T-01-14 | Tampering | manifest version scheme | high | mitigate | `manifest.json` version `2.0.0` (> 1.168.85), chosen by the user at the blocking checkpoint (D-19) | closed |
| T-01-15 | Information disclosure | committed versions.env | low | accept | See accepted risk AR-02 | closed |
| T-01-16 | Information disclosure | hosted log lines in baseline | low | mitigate | 01-VALIDATION-BASELINE.md holds only validator lines; no token or secret strings found | closed |
| T-01-17 | Spoofing | recording the wrong run | medium | mitigate | Baseline records workflow Validate, branch `ccr-ab9176f1-jbs2rg` and head commit `bd8de7a`, an ancestor of HEAD | closed |
| T-01-18 | Tampering | local vs hosted output drift | low | accept | See accepted risk AR-03 | closed |
| T-01-19 | Tampering | port commits into served JS | medium | mitigate | The only change under `card/` or `panel/` since bc7e90c is the deleted `.bak_divfix` backup; no served JS was modified | closed |
| T-01-20 | Denial of service | root translation deletion | medium | mitigate | `translations/` keeps 2,139-key parity across nine languages after the deletion | closed |
| T-01-21 | Repudiation | root translation / strings.json / backup deletion | low | mitigate | Deletion-only commits `chore(01-07): delete truncated root translations and unused strings.json` and `chore(01-07): delete the unserved calendar card .bak_divfix backup` | closed |
| T-01-SC | Tampering | pip installs into scratch venv (01-01, 01-05) | high | mitigate | Pinned `homeassistant==2026.10.4`, `infrared-protocols==10.1.0`, `tqdm==4.70.1`; venv outside the repo; nothing installed is committed. Plans 01-02/03/04/06/07 install nothing | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-10 | `hacs/action@main` and `home-assistant/actions/hassfest@master` are the docs-prescribed first-party refs for the baseline (D-22); Phase 3 pins full commit SHAs and adds Dependabot for github-actions | Plan 01-03 threat model (D-22) | 2026-10-27 |
| AR-02 | T-01-15 | `versions.env` holds only public version pins and is tracked by design; the `.env` ignore rule matches only the exact name. It must never receive secrets | Plan 01-04 threat model | 2026-10-27 |
| AR-03 | T-01-18 | The local harness result is labelled predicted and the hosted run authoritative; the Differences table records every divergence | Plan 01-05 threat model | 2026-10-27 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-27 | 22 | 22 | 0 | /gsd-secure-phase 01 (L1 grep-depth, auditor skipped by short-circuit rule) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-27
