---
status: testing
phase: 01-clean-foundation
source: [01-VERIFICATION.md]
started: 2026-10-27T07:43:01Z
updated: 2026-10-27T08:17:54Z
---

## Current Test

[testing complete]

## Tests

### 1. Confirm the FOUND-07 ordering rule (01-04 truth tagged verification: backstop): every future release version is strictly greater than the previous one and no published number is reused
expected: PROJECT.md 'Fork versioning' row states the rule (verifier observed the text); you accept that enforcement is deferred to the Phase 4 REL-01 tag check
result: pass

### 2. Resolve prohibition FOUND-04 (test tier): MUST NOT commit HA runtime state, integration backups or env files
expected: Accept the verifier evidence: 0 tracked .storage/, family_hub_backups/ or .env paths; git check-ignore confirms all three are ignored
result: pass

### 3. Resolve prohibition FOUND-05 (test tier): MUST NOT delete served brand art or make any runtime change
expected: Accept: icon.png and brand/* tracked and unchanged; git diff bc7e90c..HEAD on card/, panel/, *.py, services.yaml, de/en/es/fr translations, icon, brand shows only the .bak_divfix deletion
result: pass

### 4. Resolve prohibition FOUND-01 (test tier): MUST NOT change served card/panel JS except via a ported-hunk port commit
expected: Accept: 01-TRIAGE.md has 14 discarded rows and 'Ported hunks: none'; served card/*.js and panel/*.js are byte-identical to bc7e90c; no Python or services.yaml change
result: pass

### 5. Resolve prohibition FOUND-06 values (test tier): MUST NOT remove the Bordello Labs notice, edit LICENSE, or present the fork as original work
expected: Accept: LICENSE unchanged vs bc7e90c; README line 153 credit 'Based on [JVarhol/HA-Family-Hub]... licensed GPLv3.'; site footer keeps 'Bordello Labs' plus the upstream credit
result: pass

### 6. Resolve prohibition FOUND-06 safety (test tier): MUST NOT change domain, name, service names, websocket prefixes, card tags, storage keys or static URL paths
expected: Accept: manifest domain family_hub / name Family Hub; all *.py (incl. const.py), services.yaml and served JS unchanged vs bc7e90c
result: pass

### 7. Resolve prohibition FOUND-09 transparency (test tier): workflow carries no error suppression
expected: Accept: validate.yml has no continue-on-error or '|| true'; hosted run 40422777272 shows both jobs red
result: pass

### 8. Resolve prohibition FOUND-08 (test tier): MUST NOT set hacs.json minimum above what the code needs
expected: Accept: hacs.json homeassistant is 2024.12.0 (not 2026.10.4); config_flow.py builds FamilyHubOptionsFlow() with no argument, which needs the 2024.12 OptionsFlow.config_entry property
result: pass

### 9. Resolve prohibition FOUND-07 (test tier): MUST NOT set a manifest version <= 1.168.85 or reuse a published number
expected: Accept: manifest version 2.0.0 compares greater than (1,168,85) numerically; 2.0.0 has never been published by the fork
result: pass

### 10. Resolve prohibition FOUND-02 / FOUND-03 (test tier): MUST NOT alter any translation string or key while moving or deleting files, and MUST NOT port the 9 orphan keys
expected: Accept: move commit 3c9a703 is 5 exact renames (0 insertions, 0 deletions); de/en/es/fr in translations/ unchanged vs bc7e90c; all 9 languages have 2,139 keys with symmetric difference 0; the 9 orphan leaf names match 0 files under custom_components/
result: pass

### 11. Resolve prohibition FOUND-09 (judgment tier): MUST NOT soften, reword away or omit any validation failure
expected: Non-authoritative verifier judgment: holds. The hosted section's failure lines match the live check-run annotations line for line (MANIFEST, fh_ui, two grocy_url URL lines, CONFIG_SCHEMA warning; HACS license, issues, topics, categories warning, '3/10 checks failed'). Issues, topics and LICENSE were not changed before the run
result: pass

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
