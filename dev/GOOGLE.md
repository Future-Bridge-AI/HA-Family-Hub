# Google Calendar for Dev and Preview

This is the one-time setup that lets Family Hub DEV and Family Hub PREVIEW show the family's real week
from Google Calendar. It is written for the developer. Everything here uses **your own Google account**:
you own the Google Cloud project and the sign-in, nothing is shared with anyone else.

Read the warning first, because it is the reason for most of the safeguards:

> Dev and Preview are connected **read and write** to the real calendars you choose. A pretend event
> the seed writes lands on the family's real calendar (tagged `[DEV]` or `[PREVIEW]`), and an event you
> add, edit or delete from Dev or Preview changes the real one. Only deleting is guarded in the app
> (a loud confirm); adding and editing are not. That is why every deploy, reset and refresh first backs
> up each chosen calendar to a file you can restore from (see "Restore an event from a backup").

## 1. Create the Google Cloud project and publish the app

1. Open the Google Cloud console with your own account and create a project (any name, for example
   "Family Hub dev").
2. Enable the **Google Calendar API** for it (APIs and services > Library).
3. Configure the **OAuth consent screen**: user type **External**, an app name, your email as support
   and developer contact. Add yourself as a test user if the console asks.
4. Set **Publishing status** to **In production** (Audience > Publish app). If you leave the app in
   "Testing", Google expires every refresh token after **7 days** and the sign-in that resets keep
   would silently die every week.

When you sign in later, Google shows an **"unverified app"** warning. That is expected for an app you
made for yourself and never submitted for review: choose Advanced, then continue to the app.

## 2. Create the OAuth client

1. APIs and services > Credentials > Create credentials > OAuth client ID.
2. Application type: **Web application**.
3. Authorised redirect URI, exactly (no trailing slash, no extra spaces):
   `https://my.home-assistant.io/redirect/oauth`
4. Copy the client ID and the client secret into `tools/seed/family.local.yaml` (it is ignored by git),
   in the `google` block described in section 8. Never put them anywhere else: not in a commit, a
   chat, a screenshot or an issue.

Do not change the client ID after the first sign-in. Home Assistant derives the credential's name from
it, and the saved sign-in points at that name.

## 3. Choose the calendars

For each calendar that should appear in Dev and Preview, open Google Calendar > Settings > the calendar
> **Integrate calendar** and copy:

- the **Calendar ID** (it goes into `calendar_id`), and
- the **Secret address in iCal format** (it goes into `ical_secret_url`). Only the calendar's owner sees
  this address. Anyone who has it can read the whole calendar, so treat it like a password.

For a calendar you do not own (nobody lets you see its secret address), either ask its owner for the
address, or set `backup: ha-snapshot` for it knowingly. A snapshot is a JSON copy of that calendar's
events, read from the running Dev or Preview, instead of an iCal export. It needs the instance to be
running when the backup is taken, and it is the weaker safety net: it does not carry everything a
calendar file does.

Then decide for each calendar:

- `writable: true` only if the seed and you may add and delete events there;
- `expect_events: true` only if the seed should put its pretend events there. It needs `writable: true`.

Everything else stays disabled in Home Assistant: the seed disables every other calendar of the
account (Birthdays and Work location included) every time it runs, so they never show up in the week.

## 4. First sign-in (once per environment)

Dev and Preview each sign in separately, under the same OAuth client. Their events can never be
confused: Dev writes `[DEV]` events and Preview writes `[PREVIEW]` events.

Do this from the **Windows browser**, after the local certificate authority is trusted in Windows (the
plan 02-09 runbook shows how), because Google sends the browser back to the address you give it:

1. Run `scripts/dev-up` (Dev) or `scripts/deploy-preview <branch>` (Preview). The seed creates the
   accounts and the application credential from your family file, then stops with "Google sign-in is
   needed once for this environment". That stop is expected the first time (`deploy-preview` reports
   it as a failure of its seeding step; the new copy is already running, so carry on below).
2. Open `https://127.0.0.1:8130` for Dev, or `https://<reserved-ip>:8124` for Preview, and sign in as the
   developer's admin (the member with `admin: true` in the family file; the generated password is in
   `dev/.ha-secrets/credentials-<env>.json`).
3. Settings > Devices & services > Add integration > **Google Calendar**.
4. When `my.home-assistant.io` asks for your Home Assistant URL, enter **that same address** (the one
   from step 2). It remembers one address per browser, so switching between Dev and Preview means changing
   it there again.
5. Sign in with your Google account and allow the calendar access.
6. Run the seed again (`scripts/dev-up` or `scripts/refresh-preview`). It reloads the entry, keeps only
   the chosen calendars, and puts the tagged pretend events on the writable ones.

If the seed says "Google sign-in is needed once for this environment", this is the section it means.

## 5. What a reset keeps and what it does not

A reset (`scripts/reset-preview`, `scripts/dev-reset`) wipes everything of the environment, including
`family_hub_backups/`, but **keeps the Google sign-in**: before the wipe the Google entry is copied to
`dev/.ha-secrets/google-<env>.json` (owner-only, outside the Home Assistant folder), and after the wipe
it is written back before Home Assistant starts. The seed then recreates the application credential from
your family file and reloads the entry. You do not sign in again.

What does not survive: everything else. The family's pretend week is seeded fresh.

If a reset ever ends with the sign-in instruction anyway (the token was revoked, expired, or the
client ID changed), repeat section 4 once for that environment.

## 6. Why a sign-in can stop working, and how to revoke it

A refresh token stops working when:

- the app is in **Testing** status (7 days, see section 1);
- the token was **not used for six months**;
- you have created more than **100 refresh tokens** for the same Google account and client (Google
  silently revokes the oldest). Dev and Preview use 2 of them;
- you removed the access in your Google account.

**If the laptop is lost or stolen**, revoke the access at <https://myaccount.google.com/permissions>
(remove the app), and change the secret addresses of the chosen calendars (Integrate calendar > Reset).

## 7. Where the secrets live

| Secret | Where | Mode |
|---|---|---|
| OAuth client ID and secret, secret iCal addresses | `tools/seed/family.local.yaml` (git-ignored) | your editor |
| Saved Google sign-in (refresh token) | `dev/.ha-secrets/google-<env>.json` (git-ignored) | 0600 |
| Calendar backups | `dev/.ha-backups/<env>/<date>/` (git-ignored) | 0600 |

The tools never print a secret iCal address; they name a calendar by its `key`.

## 8. The `google` block of the family file

```yaml
google:
  client_id: "paste the client ID from step 2"
  client_secret: "paste the client secret from step 2"
  calendars:
    - key: family            # lower-case letters, digits and hyphens; members refer to it as google:family
      calendar_id: "paste the Calendar ID"
      person: Jordan          # the member (first name) this calendar belongs to
      writable: true
      expect_events: true     # needs writable: true
      backup: ical            # or ha-snapshot (default: ical)
      ical_secret_url: "https://calendar.google.com/calendar/ical/.../basic.ics"
```

| Key | Meaning |
|---|---|
| `client_id`, `client_secret` | the OAuth client of section 2 |
| `calendars[].key` | short name, `[a-z0-9-]+`; a member uses `calendar: google:<key>` |
| `calendars[].calendar_id` | the Calendar ID from Integrate calendar; must be unique |
| `calendars[].person` | first name of a member of the family file |
| `calendars[].writable` | the seed and you may write to it (default false) |
| `calendars[].expect_events` | pretend events go here (default false; needs `writable: true`) |
| `calendars[].backup` | `ical` (secret address, default) or `ha-snapshot` |
| `calendars[].ical_secret_url` | required for `backup: ical`; must start with `https://calendar.google.com/calendar/ical/` and end with `.ics` |

## 9. Restore an event from a backup

Before every `deploy-preview`, `reset-preview`, `dev-reset` and `refresh-preview`, each chosen calendar
is saved to `dev/.ha-backups/<env>/<YYYY-MM-DD_HHMMSS>/<key>.ics` (owner-only, outside the Home Assistant
folder). The save comes first: if any calendar's backup fails, is empty or is not a calendar file, the
command stops with `backup failed for <key>: <reason> - nothing was changed`, before anything is
stopped, wiped or deleted. Fix the cause (usually a changed secret address, or no internet) and run it
again. A calendar kept as `ha-snapshot` is read from the running instance, so a reset or deploy of a
stopped environment stops on it until you start the environment (or give that calendar a secret address).

To put one event back after a mistake:

1. Find the newest folder in `dev/.ha-backups/<env>/` from **before** the mistake, and open
   `<key>.ics` in it with a plain text editor.
2. Find the event (search for its title). Copy its whole block, from `BEGIN:VEVENT` down to the matching
   `END:VEVENT`.
3. Make a new file, `restore.ics`, that starts with the first lines of the backup file (everything above
   the first `BEGIN:VEVENT`, which begins with `BEGIN:VCALENDAR`), then the block you copied, then
   `END:VCALENDAR` on its own last line.
4. In Google Calendar open Settings > **Import & export** > Import, choose `restore.ics` and the
   calendar to put the event back in. Check the event is there, once.

Notes:

- Assumption A12, still to be confirmed: Google Calendar's Import should accept a file with a single
  event. Try this once on a throwaway calendar at the laptop checkpoint (plan 02-09), so the first real
  restore is not the first attempt.
- Importing adds the event again as a new copy; it does not remove the changed one, so delete the damaged
  copy by hand.
- A calendar saved with `backup: ha-snapshot` is a `<key>.json` file with that calendar's events (90 days
  back to a year ahead). It cannot be imported: read the event from it and create it again by hand.
- A backup freshness note (assumption A11): Google's secret iCal feed can lag a little behind the live
  calendar, so a change made in the last few minutes before a backup may not be in it.

### Disk use and pruning

Each backup is small (a calendar file is usually a few hundred kilobytes). Every deploy, reset and
refresh adds one dated folder per environment, so the folders add up. To prune, delete the dated folders
you no longer want (the folder name is the date), for example everything older than a month:

```
find dev/.ha-backups/preview -mindepth 1 -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +
```

Keep at least the newest folder from before any risky experiment.
