# Phase 1 Triage Record

**Date:** 2026-10-26
**Base commit:** `8b3e986` (HEAD when this record was computed; every figure below was computed from `git show HEAD:<path>`, `git rev-parse` and `git ls-files` with read-only commands, and from short `python3 -B -I` scripts that read git output only)
**Written by:** plan 01-01, Task 2, before any card, panel, translation, screenshot or icon file is deleted (D-02)

This is the auditable per-file record that plans 01-02 (port and delete cards/panels), 01-06 and 01-07 (translations, strings.json, `.bak_divfix`) rely on.

## Root card and panel duplicates

Served paths (`__init__.py` line 12503 onward) register only `card/` and `panel/`. Nothing serves or references a root-level `.js`. Version tags are the highest `1.NNN.N` string in each file, compared numerically. "Root-only lines" counts non-blank root lines whose stripped text appears nowhere in the served copy. The Outcome column is the D-01 per-file review result: `discarded` unless a root-only hunk is a self-contained fix that is missing from the served copy and newer than its version tags.

| Root file | Served copy | Root lines | Served lines | Identical | Newest version tag (root / served) | Root-only lines | Outcome | Note |
|---|---|---:|---:|---|---|---:|---|---|
| `custom_components/family_hub/family-hub-active-timers-card.js` | `custom_components/family_hub/card/family-hub-active-timers-card.js` | 1524 | 1801 | no | 1.119.0 / 1.168.79 | 127 | discarded | identical to served before upstream 8f7172d, which regressed only the root copy. Root-only hunks are the older timer-alarm singleton (`activeUid` block, root 98-288) and a few hardcoded English labels the served copy routes through `_t()` |
| `custom_components/family_hub/family-hub-chores-card.js` | `custom_components/family_hub/card/family-hub-chores-card.js` | 5869 | 6252 | no | 1.132.61 / 1.168.79 | 251 | discarded | identical to served before upstream 8f7172d, which regressed only the root copy. Root-only lines are the same older timer-alarm block (root 935-1125) plus hardcoded English strings and older markup; no root-only line carries a tag above 1.119.0 |
| `custom_components/family_hub/family-hub-goals-card.js` | `custom_components/family_hub/card/family-hub-goals-card.js` | 1784 | 1937 | no | 1.132.59 / 1.168.79 | 130 | discarded | identical to served before upstream 8f7172d, which regressed only the root copy. Root-only lines are the older timer-alarm block (root 244-434) and untranslated labels |
| `custom_components/family_hub/family-hub-my-chores-card.js` | `custom_components/family_hub/card/family-hub-my-chores-card.js` | 1538 | 160 | no | 1.132.61 / 1.168.76 | 1271 | discarded | identical to served before upstream 8f7172d, which regressed only the root copy. The served file is the deprecated shim ("DEPRECATED since v1.168.66", renders the Chores card); the root file is the retired 1,500-line card, so the served copy is smaller on purpose |
| `custom_components/family_hub/family-hub-pantry-card.js` | `custom_components/family_hub/card/family-hub-pantry-card.js` | 1600 | 1704 | no | 1.132.59 / 1.168.79 | 133 | discarded | Root-only lines are the older timer-alarm block (root 30-217); nothing else of size |
| `custom_components/family_hub/family-hub-recipe-box-card.js` | `custom_components/family_hub/card/family-hub-recipe-box-card.js` | 2896 | 3592 | no | 1.132.59 / 1.168.79 | 232 | discarded | Older timer-alarm block (root 1539-1726), an older instruction-step renderer (root 1310-1329) and an older Recipe Viewer CSS copy (root 2677-2684), all superseded in the served copy |
| `custom_components/family_hub/family-hub-rewards-card.js` | `custom_components/family_hub/card/family-hub-rewards-card.js` | 3958 | 4285 | no | 1.132.61 / 1.168.79 | 141 | discarded | Older timer-alarm block (root 872-1059) is the only hunk of size |
| `custom_components/family_hub/family-hub-todo-card.js` | `custom_components/family_hub/card/family-hub-todo-card.js` | 4310 | 4414 | no | 1.132.59 / 1.168.79 | 132 | discarded | Older timer-alarm block (root 606-793) and an older `_applyTranslations` call site (root 1294-1301) |
| `custom_components/family_hub/family-right-now-card.js` | `custom_components/family_hub/card/family-right-now-card.js` | 2047 | 2047 | yes | 1.168.79 / 1.168.79 | 0 | discarded | byte-identical to the served copy (same blob hash); deleting loses nothing |
| `custom_components/family_hub/family-screensaver-card.js` | `custom_components/family_hub/card/family-screensaver-card.js` | 1558 | 1643 | no | 1.132.61 / 1.168.76 | 125 | discarded | Older timer-alarm block (root 29-216) only |
| `custom_components/family_hub/family-today-card.js` | `custom_components/family_hub/card/family-today-card.js` | 2738 | 2901 | no | 1.132.59 / 1.168.79 | 137 | discarded | Older timer-alarm block (root 43-230) only |
| `custom_components/family_hub/family-week-calendar-card.js` | `custom_components/family_hub/card/family-week-calendar-card.js` | 23534 | 30925 | no | 1.147.0 / 1.168.85 | 1003 | discarded | Largest gap. Root-only lines are the older timer-alarm block (root 2236-2423), the older inline `<style>` block (root 9282-10767; the served copy replaced it with `FAMILY_HUB_SHARED_STYLE_BLOCK`), an older per-button child/kiosk account toggle (root 12929-12949; the served copy consolidated it into `.notify-profile-account-type-btn`) and older recipe-import markup. All are superseded implementations, none is a fix missing from the served copy |
| `custom_components/family_hub/theme-builder-panel.js` | `custom_components/family_hub/panel/theme-builder-panel.js` | 1021 | 1131 | no | none / 1.168.76 | 58 | discarded | Root-only lines are hardcoded English labels ("Save All", "Colors", "Glass blur" and so on) that the served copy now routes through translation keys. No version tag in the root file |
| `custom_components/family_hub/theme-selector-card.js` | `custom_components/family_hub/panel/theme-selector-card.js` | 320 | 320 | yes | none / none | 0 | discarded | byte-identical to the served copy (same blob hash); deleting loses nothing |

Review result: across all 14 files, the highest version tag found inside any root-only line is 1.119.0 (my-chores: 1.132.61), always older than the newest tag of its served copy. The root-only hunks fall into five groups, none of them a fix absent from the served copy: the older timer-alarm singleton, hardcoded English labels later moved to `_t()`, older inline CSS, older markup for features that were later consolidated, and (my-chores) the retired card body. No row is ambiguous.

History facts (D-01 evidence). Before upstream commit `8f7172d` (2026-10-25, "Add files via upload"), the root and served copies of active-timers, chores, goals and my-chores were byte-identical (blob hashes equal at `8f7172d^`: `5d65a19`, `afd32ba`, `78a2ff1`, `b9ea67c`). `8f7172d` then overwrote only the root copies with older content (and root `de.json`, `en.json`, `es.json`). The served copies were not touched, so none of that content ever ran in Home Assistant.

`custom_components/family_hub/card/family-week-calendar-card.js.bak_divfix`: 1244693 bytes. Outcome discarded (D-03). Referenced by no code or served file; the only tracked mentions are planning/instruction documents and `docs/onboarding-findings.md`. It is the only consumer of the 9 orphan translation keys listed below.

Ported hunks: none

## Root translations

Leaf keys are counted after a recursive flatten to full dotted paths. "Only-in-root" and "only-in-translations" are set differences against `translations/<same>.json`; "value diff" counts shared keys whose text differs.

| Root file | Leaf keys | Only in root | Only in translations | Shared-key value diffs |
|---|---:|---:|---:|---:|
| `en.json` | 1117 | 0 | 1022 | 13 |
| `de.json` | 1019 | 9 | 1129 | 6 |
| `es.json` | 1019 | 9 | 1129 | 6 |
| `fr.json` | 2139 | 0 | 0 | 0 |

`translations/en.json` has 2139 leaf keys and is the reference.

Root `it`, `nl`, `pl`, `pt`, `pt-BR` have no `translations/` copy yet. Compared with `translations/en.json`:

| Root file | Leaf keys | Symmetric difference vs `translations/en.json` |
|---|---:|---:|
| `it.json` | 2139 | 0 |
| `nl.json` | 2139 | 0 |
| `pl.json` | 2139 | 0 |
| `pt.json` | 2139 | 0 |
| `pt-BR.json` | 2139 | 0 |

`pt.json` and `pt-BR.json` are byte-identical (md5 `2c33d85a4f5e8c6c7fc1701232a652ce`, both). Both are moved as is (D-05).

### The 9 orphan keys (root `de.json` and `es.json` only)

Verbatim:

- `fh_ui.settings.chore_due_hint`
- `fh_ui.settings.chore_due_label`
- `fh_ui.settings.date_and_time`
- `fh_ui.settings.date_only`
- `fh_ui.settings.goals_in_chores_hint`
- `fh_ui.settings.goals_in_chores_label`
- `fh_ui.settings.goals_in_rewards_hint`
- `fh_ui.settings.goals_in_rewards_label`
- `fh_ui.settings.small_screen_mode_hint`

Proof: `git grep -w -l <leaf name> HEAD -- . ':!.planning' ':!.claude'` returns exactly three files for each of the nine leaf names: `custom_components/family_hub/card/family-week-calendar-card.js.bak_divfix`, `custom_components/family_hub/de.json` and `custom_components/family_hub/es.json`. No served `.js` or `.py` file matches. Outcome: not ported (D-06). They are recorded here in case upstream later ships the feature they belonged to.

### Root de, en, es, fr: nothing served is lost

Root `de.json`, `en.json`, `es.json` and `fr.json` are deleted in plan 01-07 (D-07). The `translations/` copies are the served ones and the newer wording; the 9 orphan keys above are the only content present in root and absent from `translations/`.

Shared-key value differences (the `translations/` wording is kept):

- root `en` vs `translations/en` (13): `config.step.calendars.data.calendars`, `config.step.calendars.description`, `config.step.calendars.title`, `config.step.member_profile.description`, `config.step.member_profile.title`, `fh_ui.add_event.reminder_hint`, `fh_ui.settings.calendars_tap_hint`, `fh_ui.settings.chores_rewards_color_hint`, `fh_ui.today.add_event.reminder_hint`, `options.abort.export_done`, `options.abort.no_backups`, `options.step.export_backup.description`, `options.step.restore_backup_pick.description`.
- root `de` and root `es` vs their `translations/` copies (6 each): `fh_ui.add_event.reminder_hint`, `fh_ui.settings.calendars_tap_hint`, `fh_ui.settings.chores_rewards_color_hint`, `fh_ui.settings.small_screen_mode_label`, `fh_ui.today.add_event.reminder_hint`, `fh_ui.todo.create_modal.no_lists`. The root `small_screen_mode_label` wording belongs to the same retired feature as the orphan keys.

### strings.json key diff

Compared: every leaf of `custom_components/family_hub/strings.json` as a full dotted path, against the union of the full dotted leaf paths of `translations/de.json`, `translations/en.json`, `translations/es.json` and `translations/fr.json`. Bare leaf names were not compared. Script output, verbatim:

```
strings.json leaf keys: 566
strings.json-only keys: 2
fh_ui.settings.reminders_hint_html
fh_ui.settings.section_reminders
```

The result equals the research expectation (566 and 2 keys). `strings.json` is read by no code (custom integrations do not read it); it is deleted per D-08 in plan 01-07. The `PROJECT_CONTEXT.md` convention of keeping `strings.json` in sync with `translations/en.json` is retired.

The `fh_ui` key group is preserved unchanged (D-09): it is not valid hassfest schema, but it is how the cards load their text and is not touched in Phase 1.

## Screenshots folder

All 15 tracked files under `\Screenshots/` (the folder name starts with a literal backslash; `git ls-files` shows it quoted). Equivalents are the files named in `images/readme/` or `website/static/img/screenshots/`.

| `\Screenshots/` file | Bytes | Equivalent present |
|---|---:|---|
| `Main Calendar.png` | 289218 | `images/readme/view-planner.webp`, site `calendar-week.webp` |
| `Month View.png` | 118737 | `images/readme/view-month.webp`, site `calendar-month.webp` |
| `Calendar Mobile.png` | 228911 | `images/readme/phone.webp`, site `calendar-phone.webp` |
| `Chores.png` | 61135 | `images/readme/card-chores.webp`, site `chores.webp` |
| `Rewards.png` | 76458 | `images/readme/card-rewards.webp`, site `rewards.webp` |
| `Family Today Card.png` | 26911 | `images/readme/card-today.webp`, site `today-card.webp` |
| `Shopping List.png` | 19412 | `images/readme/card-todo.webp`, site `todo-lists.webp` |
| `Add Modal Main Screen.png` | 15810 | site `add-event.webp` only |
| `Recipe Box.png` | 89175 | site `recipe-box.webp` only |
| `My Chores and My Goals Mini Cards.png` | 33684 | site `my-chores.webp` only (card is deprecated) |
| `Import Recipe to Grocy.png` | 99183 | none |
| `Screen Saver Card.png` | 80805 | none |
| `Chores Mobile View.jpg` | 247874 | none (closest: `phone.webp`) |
| `Rewards Mobile View.jpg` | 132525 | none |
| `screenshots.txt` | 1 | n/a (1-byte placeholder) |

No equivalent (listed before deletion, D-11):

- `Import Recipe to Grocy.png`
- `Screen Saver Card.png`
- `Chores Mobile View.jpg`
- `Rewards Mobile View.jpg`

No tracked file links to the folder. Grep proof: `git grep -nE 'Screenshots/|\\Screenshots|%5CScreenshots' HEAD -- . ':!.planning' ':!.claude'`, with unrelated `/img/screenshots/` site paths filtered out, matches only three prose lines in `docs/onboarding-findings.md` (an audit note that calls the folder a hygiene problem). The README's "Screenshots" anchor points at its own `#a-look-around` section.

## Icons and readme

md5 and size of the root image files and the four `brand/` images, from `HEAD` blobs:

| File | Bytes | md5 |
|---|---:|---|
| `custom_components/family_hub/icon.png` (served) | 20875 | `aa5ee4ba0f0ab23d340b571eb2dc3ad9` |
| `custom_components/family_hub/icon (1).png` | 20875 | `aa5ee4ba0f0ab23d340b571eb2dc3ad9` |
| `custom_components/family_hub/icon@2x.png` | 50405 | `5e65843d4f1702790a578ec995f858ca` |
| `custom_components/family_hub/logo.png` | 20875 | `aa5ee4ba0f0ab23d340b571eb2dc3ad9` |
| `custom_components/family_hub/logo@2x.png` | 50405 | `5e65843d4f1702790a578ec995f858ca` |
| `custom_components/family_hub/brand/icon.png` | 20875 | `aa5ee4ba0f0ab23d340b571eb2dc3ad9` |
| `custom_components/family_hub/brand/icon@2x.png` | 50405 | `5e65843d4f1702790a578ec995f858ca` |
| `custom_components/family_hub/brand/logo.png` | 20875 | `aa5ee4ba0f0ab23d340b571eb2dc3ad9` |
| `custom_components/family_hub/brand/logo@2x.png` | 50405 | `5e65843d4f1702790a578ec995f858ca` |

Only two distinct images exist. Keep root `icon.png`: it is served as `ICON_URL` (`__init__.py` line 12550, `icon_path = f"{integration_dir}/icon.png"`, guarded by `os.path.isfile`, so a deletion would fail silently and the sidebar panel would lose its icon). Keep the whole `brand/` folder (HA and HACS brand assets) (D-12). Delete the four unserved root duplicates `icon (1).png`, `icon@2x.png`, `logo.png`, `logo@2x.png`.

The one allowed duplicate pair is root `icon.png` (served) and `brand/icon.png` (HACS brand check). The "no duplicate icon files" success criterion is satisfied with that exception stated.

`custom_components/family_hub/readme.md` is 1 byte (md5 `68b329da9893e34099c7d8ad5cb9c940`) and is deleted (D-13). HACS renders the repo-root `README.md` (`render_readme: true`).

## Upstream sync rule

Per D-18: there is no ongoing upstream sync in this milestone. Any future upstream pull must map root-file edits onto `card/`, `panel/` and `translations/`, because only those locations are served. Upstream "Add files via upload" commits sometimes touch only the root copies and sometimes both:

- `8f7172d` edited only root copies (active-timers, chores, goals and my-chores cards, and root `de.json`, `en.json`, `es.json`), replacing them with older content. Served copies were untouched.
- `74bb966` edited both the root and the served copy.

A future pull that brings in a root-level file must be compared against the served copy first, and applied there, never to the root path.
