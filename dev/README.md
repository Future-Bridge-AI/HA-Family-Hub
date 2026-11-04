# Dev and Family Preview

This is the developer's runbook for the two Home Assistant instances that run on your Windows 11
laptop: **Dev**, where you change the code, and **Preview**, where the family product owner tries a
change before it reaches the real Home. Neither one is the family's real Home Assistant, and neither
one can touch it.

## What runs where

| | Dev | Preview |
|---|---|---|
| Address | `https://127.0.0.1:8130` | `https://<reserved-ip>:8124` |
| Who can reach it | only this laptop (bound to loopback) | the home network, so her phone can open it |
| Name on screen | Family Hub DEV | Family Hub PREVIEW |
| Code | your working copy, mounted read-only | an exported copy of one git ref, stamped with a version line |
| Config volume | `dev/.ha-dev` | `dev/.ha-preview` |

Both run Home Assistant 2026.10.4 (the pin in `versions.env`) in Docker Engine inside WSL2. Use
`127.0.0.1`, not `localhost`, from the Windows browser. Host-specific values (time zone, the reserved
address, the WSL distribution name) live in `dev/host.env`, which git ignores.

What each script does:

- `scripts/dev-up`, `dev-cards`, `dev-restart`, `dev-down`, `dev-reset`: start Dev, make card edits show up,
  pick up Python edits, stop Dev, erase and re-seed Dev.
- `scripts/deploy-preview <ref>`: put a committed git ref on Preview, check Home Assistant serves it, and
  print the note to pass on to her.
- `scripts/reset-preview`: erase Preview and bring back the starting week.
- `scripts/refresh-preview`: top up the week without erasing anything (scheduled, see below).
- `scripts/preview-down`: stop Preview.
- `scripts/doctor`: check this laptop and say exactly what is wrong.
- `scripts/make-certs`: create the local certificate authority and the HTTPS certificate.
- `scripts/windows/setup-host.ps1`: the one-time Windows side (run elevated, from Windows).

## One-time laptop setup

You need Windows 11 22H2 or later (mirrored networking needs it), a Google account of your own for the
calendars (see `dev/GOOGLE.md`), and access to the router's admin page.

1. **WSL and Ubuntu.** Install WSL from the Microsoft Store, then Ubuntu (`wsl --install -d Ubuntu`) and
   create your Linux user. Write down the output of `wsl --version`. Do not run `wsl --update` between
   try-out sessions: some builds break Docker ports in mirrored mode, so update only on purpose, when
   nobody is trying anything.
2. **systemd.** In Ubuntu, `sudo nano /etc/wsl.conf` and make sure it contains:

   ```
   [boot]
   systemd=true
   ```

   Then in Windows PowerShell run `wsl --shutdown` and open Ubuntu again.
3. **Docker Engine inside Ubuntu.** Follow Docker's own instructions for Ubuntu (install Docker Engine
   from Docker's apt repository, including the compose plugin). **Not Docker Desktop.** Then
   `sudo systemctl enable --now docker` and `sudo usermod -aG docker $USER`, and open a new Ubuntu
   window so the group applies.
4. **Clone the repository into your Ubuntu home directory**, for example
   `git clone https://github.com/Future-Bridge-AI/HA-Family-Hub.git ~/HA-Family-Hub`. Never under
   `/mnt/c` (a Windows drive): file permissions for secrets and speed are wrong there, and
   `scripts/doctor` refuses it. Clone with Linux git inside Ubuntu, not with Windows git, so the scripts
   keep Unix line endings.
5. **Random hardware addresses off, and a reserved address.** Preview's certificate and her phone's
   address depend on the laptop always having the same address, so settle that first:
   - Windows Settings > Network & internet > Wi-Fi > your home network > Properties >
     **Random hardware addresses = Off**. Disconnect and reconnect to the Wi-Fi.
   - In the router's admin page make a **DHCP reservation** for the laptop's Wi-Fi adapter. Check the
     reservation lists the adapter's real hardware address (Settings shows it on the same page), not a
     random one.
   - Reconnect, then note the laptop's Wi-Fi address (for example `192.168.50.10`).
6. **Host file.** `cp dev/host.env.example dev/host.env`, then edit it: your time zone and place, and the
   reserved address as `PREVIEW_HOST_IP`. Nothing in `dev/host.env` is ever committed.
7. **Certificates.** `scripts/make-certs` creates the local certificate authority (`ca.crt`, `ca.key`)
   and an HTTPS certificate for the reserved address, in `dev/.ha-certs`. It runs once; running it again
   reuses the same authority.
8. **The Windows side.** Open Windows PowerShell **as administrator** and run the setup script (change
   `<you>` to your Linux user, and `Ubuntu` if your distribution has another name):

   ```
   powershell -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu\home\<you>\HA-Family-Hub\scripts\windows\setup-host.ps1"
   ```

   It sets mirrored networking in `.wslconfig` (keeping a dated copy of the old file), creates one
   Hyper-V firewall rule for port 8124 only, registers the three scheduled tasks ("FamilyHub WSL
   keep-alive", "FamilyHub refresh at logon", "FamilyHub refresh daily"), adds `ca.crt` to your trusted
   roots (Windows may ask you to confirm: answer Yes), and reports whether the Wi-Fi is a Private network.
   Options: `-Distro`, `-RepoPath`, `-DailyTime` (default 05:30), `-RemoteSubnet` (limit the rule to the
   home network, for example `192.168.50.0/24`), `-SkipCaImport`. It is safe to run again.
9. **Restart WSL.** In PowerShell run `wsl --shutdown`, wait 8 seconds, open Ubuntu again.
10. **Check.** Run `scripts/doctor` in Ubuntu until there is no FAIL line. WARN lines are explained in
    their message. If something stays FAIL, go down the "Fallback ladder" below, in order.
11. **Dev.** `scripts/dev-up`, then open `https://127.0.0.1:8130` in the Windows browser. There must be
    no certificate warning.
12. **Google.** Follow `dev/GOOGLE.md` (sections 1 to 4).

Preview is up only while your Windows user is logged in and the laptop is awake: the keep-alive task
starts when you log on. Leave the laptop plugged in, logged in and on the home Wi-Fi on the days she is
trying things.

## Daily use

| Command | What it does |
|---|---|
| `scripts/dev-up` | start Dev (safe to run again) |
| `scripts/dev-cards` | after editing a card in `custom_components/family_hub/card/`, re-register the card files so a normal browser refresh loads them |
| `scripts/dev-restart` | after editing Python, restart Dev's container and wait until it answers |
| `scripts/dev-down` | stop Dev (its data stays) |
| `scripts/dev-reset [--yes]` | erase Dev and re-seed it; asks you to type DEV |
| `scripts/deploy-preview <branch\|tag\|commit> [--what TEXT] [--view NAME] [--tap TEXT]` | put a committed ref on Preview; `--what` is one sentence on what changed, `--view` the screen to open, `--tap` what to tap; prints the hand-off note to pass on to her |
| `scripts/reset-preview [--yes]` | erase Preview and re-seed it; asks you to type PREVIEW; her phone may ask her to sign in again |
| `scripts/refresh-preview [--yes]` | top up the week and sync the pretend events without erasing anything; this is what the scheduled tasks run |
| `scripts/preview-down` | stop Preview |
| `scripts/doctor` | check the laptop |

Only committed work is deployed: `deploy-preview` exports the ref with `git archive`, so uncommitted edits
never reach Preview. Every deploy, reset and refresh first backs up the chosen Google calendars and stops
if a backup is not a real calendar file (see `dev/GOOGLE.md`, "Restore an event from a backup").

## Leaving home

Run `scripts/preview-down` before taking the laptop to a network that is not home: Preview is published
on the home network, and on any other Wi-Fi its login page would be reachable. Back at home, start it
again with `scripts/deploy-preview <branch>` (or `scripts/reset-preview`): a Preview you stopped on
purpose does not come back by itself, and the scheduled refresh then reports "Preview is not running"
and does nothing. (A Preview that was only interrupted by WSL or Docker restarting does come back by
itself.) **Never port-forward 8124** on the router: Preview is for the home network only.

## Google calendars

The real family calendars are connected through your own Google Cloud project and sign-in. All the steps,
what a reset keeps, how to revoke access and how to restore an event from a backup are in
[dev/GOOGLE.md](GOOGLE.md).

## Her phone

Only `dev/.ha-certs/ca.crt` goes on her phone, never any `.key` file. Copy it to the phone and install it
as a CA certificate (on Android: Settings > Security > Encryption and credentials > Install a certificate
> CA certificate; the menu words differ between makers, so write down what yours says). Then open
`https://<reserved-ip>:8124` in Chrome: the Home Assistant login page must load with no certificate
warning. If it shows one, go to "Certificate rejected" below.

In the Home Assistant app, turn off sensors and location sharing for the Preview server (Settings >
Companion app > the Preview server): the app can otherwise share the phone's sensors with every server it
knows, and Preview must not hold a real phone's data. The full steps for her are in
`docs/family/getting-started.md`.

## Fallback ladder

If her phone cannot reach `https://<reserved-ip>:8124`, take these steps in order and stop at the first
one that fixes it. Write down which one you needed in `.planning/phases/02-dev-family-preview/02-BRINGUP.md`.

1. **Re-check the basics.** The Hyper-V rule exists (`Get-NetFirewallHyperVRule -Name FamilyHubPreview`
   in an elevated PowerShell), the Wi-Fi is a Private network (setup-host.ps1 reports it), ports 8124
   and 8130 are not inside a Windows excluded port range (`netsh interface ipv4 show excludedportrange
   protocol=tcp`), and `wsl --version` is not a build with known trouble (`scripts/doctor` warns on
   2.9.x). `scripts/doctor` checks all of these.
2. **`hostAddressLoopback=true`.** In `%UserProfile%\.wslconfig` add a section `[experimental]` with
   `hostAddressLoopback=true`, then `wsl --shutdown`. This is the documented lever when Windows cannot
   reach a container's port through the laptop's own address.
3. **Move off a regressed WSL build.** If published ports fail to bind on a 2.9.x build, install a
   WSL release that is not affected (a deliberate `wsl --update`, or the older release from
   github.com/microsoft/WSL/releases), then `wsl --shutdown`.
4. **NAT plus a port proxy.** Set `networkingMode=nat` (or remove the line) in `.wslconfig`, and add a
   `portproxy` rule on Windows for 8124 that you refresh at every WSL start, because the WSL address
   changes between starts: `netsh interface portproxy add v4tov4 listenport=8124 listenaddress=0.0.0.0
   connectport=8124 connectaddress=<address from hostname -I in Ubuntu>`. This needs a small script that
   runs at logon; the Hyper-V rule does not apply in NAT mode, so a normal Windows Defender inbound rule
   for 8124 is needed instead.
5. **`network_mode: host` for Preview only.** Last resort, and an explicit decision: it departs from the
   plan that Preview runs in its own bridge network. Do not do it silently; record the decision and the
   reason in `02-BRINGUP.md`.

## Certificate rejected

If the phone's browser or the Home Assistant app shows a certificate error after `ca.crt` is installed,
take these steps in order. Every step keeps HTTPS.

1. **Check the app and the chain.** The Home Assistant app must be 2026.6.5 or later. Check the leaf is
   signed directly by the root, with no intermediate in between (an Android app issue with intermediates
   of a custom root): `openssl x509 -in dev/.ha-certs/leaf.crt -noout -issuer` must name `Family Hub local
   CA`. Then remove `ca.crt` from the phone and install it again as a **CA certificate**.
2. **An unconstrained local CA for the home network only.** The certificate authority is limited to
   private addresses and `localhost` (a name constraint), and some phones refuse that. Re-run make-certs
   without name constraints: delete `dev/.ha-certs/ca.*` and `dev/.ha-certs/leaf.*`, remove the
   `nameConstraints` line and the `[name_constraints]` block from the CA settings inside
   `scripts/make-certs` for this one run, run `scripts/make-certs`, restore the file with
   `git checkout -- scripts/make-certs`, install the new `ca.crt` on the phone and in Windows
   (`scripts/windows/setup-host.ps1`), and restart Dev and Preview. This is a recorded trade-off
   (research Open Question 5): anyone who got `ca.key` could then vouch for any website for the devices
   that trust it, so `ca.key` must never leave the laptop and the CA is for the home network only. Write
   the decision in `02-BRINGUP.md`.
3. **Chrome "Add to Home screen".** Open `https://<reserved-ip>:8124` in Chrome on the phone and choose
   Add to Home screen. That gives her a one-tap icon on the same HTTPS address while the app still
   rejects the certificate.
4. **A publicly trusted certificate** on a domain you own, pointed at the reserved address (a public
   certificate authority's certificate needs no installation on any phone). Tailscale HTTPS stays
   deferred (ENVX-01).

Plain HTTP is never applied by any script and is never a silent fallback. It is possible only as an
explicit developer decision, written into `02-BRINGUP.md` with the reason.

## Security notes

- `ca.key` never leaves this laptop. Only `ca.crt` is copied to a phone or imported into Windows.
- `dev/.ha-secrets`, `dev/.ha-certs/*.key` and the saved Google sign-in are owner-only (0700 and 0600);
  `scripts/doctor` checks it. They are git-ignored; never commit, paste or screenshot them.
- Preview is for the home network: never port-forward 8124, and run `scripts/preview-down` away from home.
- If the laptop is lost or stolen, revoke the Google access (see `dev/GOOGLE.md`, section 6) and remove
  the Family Hub local CA from her phone.

## Bring-up record

Filled in after the first laptop bring-up (plan 02-09).
