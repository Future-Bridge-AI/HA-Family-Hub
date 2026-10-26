# Phase 1: Clean Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-26
**Phase:** 01-clean-foundation
**Mode:** `--auto` — recommended option auto-selected for every question; no user prompts.
**Areas discussed:** Root duplicate triage, Orphan translation keys, Root translations & strings.json, Screenshots folder, Icons, Fork identity, Version scheme, Minimum HA version, Validation baseline, Commit structure

`[--auto] Selected all gray areas: Root duplicate triage, Orphan translation keys, Root translations & strings.json, Screenshots folder, Icons, Fork identity, Version scheme, Minimum HA version, Validation baseline, Commit structure.`

---

## Root duplicate triage

| Option | Description | Selected |
|--------|-------------|----------|
| Diff, default-delete, port only self-contained fixes | Served copies are newer and live; record outcome per file | ✓ |
| Port everything root-only | Risks reintroducing stale/older code into served cards | |
| Delete without review | Fast but loses any genuine root-only fix silently | |

**Choice:** [auto] Diff, default-delete, port only self-contained fixes (recommended default).

## Orphan translation keys (9 in root de/es)

| Option | Description | Selected |
|--------|-------------|----------|
| Don't port; record in triage | Only consumer is `.bak_divfix` debris (verified by grep) | ✓ |
| Port into all translations | Dead keys no served code uses | |

**Choice:** [auto] Don't port; record (recommended — based on verified grep).

## Root translations & strings.json

| Option | Description | Selected |
|--------|-------------|----------|
| Move it/nl/pl/pt/pt-BR; delete truncated root de/en/es/fr and strings.json; keep `fh_ui` | Exact key parity verified | ✓ |
| Keep strings.json in sync | Custom integrations don't read it | |

**Choice:** [auto] Move + delete, keep `fh_ui` (recommended).

## Screenshots folder

| Option | Description | Selected |
|--------|-------------|----------|
| Delete `\Screenshots/` | `images/readme/` already serves README/site; no references found | ✓ |
| Rename to `screenshots/` | Keeps a second, unused screenshot set | |

**Choice:** [auto] Delete, listing any unique image first (recommended).

## Icons

| Option | Description | Selected |
|--------|-------------|----------|
| Keep served root `icon.png` + `brand/`; delete identical unserved root dupes | md5-verified duplicates | ✓ |
| Delete all root images | Breaks `ICON_URL` | |

**Choice:** [auto] Keep served + brand, delete dupes (recommended).

## Fork identity

| Option | Description | Selected |
|--------|-------------|----------|
| Change links/codeowner/docs config only; keep domain, services, ws prefixes, card tags | Avoids orphaning saved dashboards | ✓ |
| Also rename domain/name | Breaks every existing install | |

**Choice:** [auto] Links/codeowner only; codeowner `@Future-Bridge-AI` (authenticated GitHub login).

## Version scheme

| Option | Description | Selected |
|--------|-------------|----------|
| Continue upstream numbering, next 1.169.0, tags `vX.Y.Z` = manifest | HACS sees it as an upgrade | ✓ |
| Own scheme (e.g. 2.0.0 or 0.x) | 0.x looks like a downgrade; 2.0.0 implies breaking change | |

**Choice:** [auto] Continue, 1.169.0 (recommended by research).

## Minimum HA version

| Option | Description | Selected |
|--------|-------------|----------|
| Set `hacs.json` to the real code minimum (~2024.7+, verified); pin 2026.10.4 for Dev/Preview/tests | Doesn't block an older Home HA | ✓ |
| Raise `hacs.json` to 2026.10.4 | Could block Home from updating | |
| Leave 2024.1.0 | Wrong for `StaticPathConfig` | |

**Choice:** [auto] Real minimum + separate pin. Note: research suggested raising to the tested version; chose the safer option for the family's Home instance, whose HA version is unknown.

## Validation baseline

| Option | Description | Selected |
|--------|-------------|----------|
| Add non-blocking `validate.yml`, run once, record failures | Real list for Phase 3; no blanket continue-on-error | ✓ |
| Run locally only | hassfest could not be run in the research sandbox | |

**Choice:** [auto] Non-blocking workflow + `01-VALIDATION-BASELINE.md` (recommended).

## Commit structure

| Option | Description | Selected |
|--------|-------------|----------|
| One logical change per commit | Independently revertible | ✓ |
| Single cleanup commit | Hard to review/revert | |

**Choice:** [auto] One per concern (recommended).

---

## Claude's Discretion

- Credit-line wording, triage/baseline doc wording, how to verify API introduction dates, `versions.env` format.

## Deferred Ideas

- Fixing hassfest/HACS failures and required checks (Phase 3); CI guards (Phase 3); `fh_ui` relocation decision (Phase 3); Node 20 bump for docs deploy (Phase 3); changelog reconciliation (Phase 4).
