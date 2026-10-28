# Phase 1: Clean Foundation - Pattern Map

**Mapped:** 2026-10-26
**Files analyzed:** 9 created/edited (deletions and moves need no analog)
**Analogs found:** 6 / 9

All analog paths verified git-tracked (`git ls-files`).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `.github/workflows/validate.yml` (new) | config (CI) | event-driven | `.github/workflows/deploy-docs.yml` | role-match |
| `custom_components/family_hub/manifest.json` | config | n/a | itself (edit in place) | exact |
| `hacs.json` | config | n/a | itself | exact |
| `README.md` (badges, links, credit) | docs | n/a | itself (lines 4-7, 149-153) | exact |
| `website/docusaurus.config.js` | config | n/a | itself | exact |
| `.gitignore` | config | n/a | itself (6 lines today) | exact |
| `versions.env` (new, repo root) | config | n/a | none | no analog |
| `01-TRIAGE.md` (new) | phase artifact | n/a | none | no analog |
| `01-VALIDATION-BASELINE.md` (new) | phase artifact | n/a | none | no analog |

## Pattern Assignments

### `.github/workflows/validate.yml` (CI, event-driven)

**Analog:** `.github/workflows/deploy-docs.yml`

Copy these conventions: top-level `name:`, `on:` with `workflow_dispatch: {}`, least-privilege `permissions:` block, `runs-on: ubuntu-latest`, `actions/checkout@v4` (lines 1-9, 11-14, 22, 27):
```yaml
name: Deploy docs site to GitHub Pages
on:
  push:
    branches: [main]
    paths:
      - 'website/**'
  workflow_dispatch: {}
permissions:
  contents: read
```
Differences for validate.yml:
- Do NOT reuse the `concurrency: group: pages` block (line 16-18). Use no group or a distinct one so the workflows cannot interfere.
- Do NOT use a `paths:` filter. Validation should run on push, pull_request and `workflow_dispatch`.
- Needs only `contents: read` (no `pages`/`id-token`).
- Two jobs (hassfest, hacs), each `actions/checkout@v4` then the action:
```yaml
jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master
  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
```
- No `continue-on-error` (D-22). Non-blocking means "not a required check", not a swallowed failure.

### `custom_components/family_hub/manifest.json` (edit lines 5, 18, 19, 21)
```json
"codeowners": ["@Future-Bridge-AI"],            // line 5 (currently @bordello_labs)
"documentation": "https://github.com/Future-Bridge-AI/HA-Family-Hub",
"issue_tracker": "https://github.com/Future-Bridge-AI/HA-Family-Hub/issues",
"version": "1.169.0"                            // line 21 (currently 1.168.85)
```
Keep the 2-space indent and one array item per line, as in the file now. Leave `domain` and `name` untouched (D-17). Keys are alphabetical-ish, with `domain`, `name` first; hassfest wants that ordering, so do not reorder.

### `hacs.json` (edit line 4)
```json
{
  "name": "Family Hub",
  "render_readme": true,
  "homeassistant": "<verified minimum, expected 2024.7.0>"
}
```
Currently `2024.1.0`. Only the `homeassistant` value changes. Do not set it to 2026.10.4.

### `README.md` (badges lines 4-7, license section 149-153)
Replace `JVarhol/HA-Family-Hub` with `Future-Bridge-AI/HA-Family-Hub` in all four badge lines, e.g. line 4:
```html
<a href="https://github.com/JVarhol/HA-Family-Hub/releases/latest"><img src="https://img.shields.io/github/v/release/JVarhol/HA-Family-Hub?style=for-the-badge&color=5da3a6" alt="Release"></a>
```
Both the href and the shields.io path need changing (two occurrences per line). Run `grep -n JVarhol README.md` to catch the HACS one-click links and body links. Add the upstream credit near the `## License` section (line 149), which already states GPL-3.0:
```markdown
Based on [JVarhol/HA-Family-Hub](https://github.com/JVarhol/HA-Family-Hub) by its original author, licensed GPLv3.
```
That credit line is the one intentional remaining `JVarhol` reference.

### `website/docusaurus.config.js`
Edit points (from grep): line 21 `url: 'https://jvarhol.github.io'` becomes `'https://future-bridge-ai.github.io'`; line 24 `organizationName: 'JVarhol'` becomes `'Future-Bridge-AI'`; lines 60 (`editUrl`), 97 (navbar), 124 (issues), 133 (footer repo), 137 (releases) all take `https://github.com/Future-Bridge-AI/HA-Family-Hub...`. Keep `baseUrl: '/HA-Family-Hub/'` and `projectName` unchanged (the fork repo name is the same). Footer credit line goes in the existing `footer` links/copyright block if one fits.

### `.gitignore` (append)
Current content, whole file:
```
__pycache__/
*.pyc
.pytest_cache/
node_modules/
.DS_Store
*.zip
```
Style: one bare pattern per line, no comments. Append:
```
.env
*.bak*
family_hub_backups/
.storage/
dev/.ha-*
```
`__pycache__/` is already ignored, so the pyc problem is purely `git rm -r --cached`.

## No Analog Found

| File | Role | Note |
|---|---|---|
| `versions.env` | config | No env or version-pin file exists. Plain `KEY=value` lines (no `export`, no quotes) so it works for `source`, `docker compose --env-file`, and GitHub Actions `$GITHUB_ENV`. Suggested: `HA_VERSION=2026.10.4`, `PYTHON_VERSION=3.14`. Add one comment line saying that pytest-homeassistant-custom-component 0.13.375 pins it. |
| `01-TRIAGE.md` | artifact | Per-file table (`file | served counterpart | outcome kept/ported/discarded | note`). Sections: root JS, root translations key diff, 9 orphan keys, `\Screenshots` images with no `images/readme/` equivalent, icons, and the upstream-sync note (D-18). |
| `01-VALIDATION-BASELINE.md` | artifact | Sections: workflow run link and date, hassfest failures, HACS failures, manual repo-settings steps (Issues enabled, description, topics; D-23). |

## Shared Patterns

- **Identity swap**: `JVarhol` becomes `Future-Bridge-AI` everywhere except the credit line. Verify with `git grep -n JVarhol` after the change. The earlier plan item is to confirm no Python or JS uses it at runtime.
- **One logical change per commit** (D-24), with deletions separate from ports (D-04).
- **Do not import or compile the integration** (it rewrites tracked `.pyc`). Do the `.pyc` untracking first, so later steps stay clean.

## Metadata

**Analog search scope:** `.github/`, repo root config files, `custom_components/family_hub/manifest.json`, `website/docusaurus.config.js`, `README.md`
**Pattern extraction date:** 2026-10-26
