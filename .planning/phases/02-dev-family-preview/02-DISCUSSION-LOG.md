# Phase 2: Dev + Family Preview - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-27
**Phase:** 02-dev-family-preview
**Areas discussed:** Preview host & address, Pretend family & seed week, Her way in & what she sees, Change hand-off & guide

---

## Preview host & address

| Option | Description | Selected |
|--------|-------------|----------|
| New mini PC | N100-class box, Debian + Docker | |
| Existing home server/NAS | Machine already running 24/7 | |
| Raspberry Pi 4/5 | Low power, ARM | |
| Not decided yet | Host-agnostic tooling | |

**User's choice:** Asked whether a cloud service is suitable (for both Preview and Home). After the trade-offs were explained (Preview: workable with Tailscale and a recorded locality exception; Home: not advised for privacy and offline reasons), the user chose "Local machine I already have": the Dev laptop for now, possibly ported to other hardware later.

| Question | Options | Selected |
|----------|---------|----------|
| Always-on vs laptop | Accept for now / Keep laptop always on / Buy a box first | Accept for now |
| Stable address | Router IP reservation / .local hostname / You decide | Router IP reservation |
| Portability | Fresh seed on new host / Move the volume too | Fresh seed on new host |
| Home hardware | Own local device, Phase 4 / Not sure yet | Not sure yet |
| HTTP vs HTTPS | HTTP, research first / HTTPS from day one | HTTPS from day one |

---

## Pretend family & seed week

| Question | Options | Selected |
|----------|---------|----------|
| Who is the family | Real first names / Invented family / Real names kept out of git | Real names, kept out of git |
| How busy | Typical / Light / Busy stress-test | Free text: "I want to use actual family calendar (google based)" |
| Calendar approach | Snapshot copy (recommended) / Read-only live feed / Full Google connection / Stay pretend | Full Google connection (3) |
| Guardrails (multi) | Back up before risky steps / Seed never writes to Google / Loud warning on delete / Keep re-sign-in out of reset | Backup, keep sign-in across reset, loud delete warning |
| Which calendars | All / Shared only / A chosen list | A chosen list |
| Seed writes to Google | Never (recommended) / Yes, tagged pretend events / No pretend events | Yes, tagged pretend events |
| Accounts | Every family member / Just you and her | Every family member |
| Extras | Core + a little of each / Core only / You decide | Core + a little of each |

**Notes:** The user was told that the real-calendar choice overrides the project's "Preview never touches real calendars" rule, and that Family Hub can delete real events. The user confirmed option 3 anyway and chose guardrails.

---

## Her way in & what she sees

| Question | Options | Selected |
|----------|---------|----------|
| How she opens Preview | Companion 2nd server / Home-screen shortcut / Phone + tablet | Companion 2nd server |
| PREVIEW look | Name + distinct theme / Plus banner strip / Just the name | Name + distinct theme |
| Dashboard contents | Mirror upstream layout / Calendar only / You decide | Mirror upstream layout |
| Dev uses Google too | No, Dev stays pretend (recommended) / Yes, same as Preview | Yes, same as Preview |
| Her phone | iPhone / Android / Both | Android |

---

## Change hand-off & guide

| Question | Options | Selected |
|----------|---------|----------|
| How she learns a change is ready | You tell her / Notice in Preview / Both | You tell her |
| Build stamp | Small footer text / More menu / Plain words only | Small footer text |
| Guide format | Markdown in docs/family/ / Also docs site / Printed one-pager | Markdown in docs/family/ |
| First visible change | She picks it / Calendar title text / You decide | She picks it |

---

## Claude's Discretion

- Tag wording for seeded Google events, local family-file schema and path
- Which built-in theme marks Preview
- Certificate tooling
- Mechanism for the Dev/Preview-only delete warning
- Layout of `dev/`, `tools/seed/`, `scripts/`

## Deferred Ideas

- Dedicated always-on hardware for Preview
- Home hardware choice (Phase 4)
- Wall-tablet kiosk access (v2 ENVX-02)
- Publishing the family guide on the docs site
- PREVIEW banner strip
