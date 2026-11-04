"""Stub-orchestration tests for the Preview and Dev scripts.

Docker cannot run in the sandbox, so a stub ``docker`` and a stub seed command (FH_SEED_CMD) on PATH
write every call to one log, in order. The scripts run for real against a temp FH_STATE_DIR and a
temp host.env, so nothing here touches dev/.ha-* or the real host settings. The seed stub hands the
``note`` command to the real tool (it needs no Home Assistant), so the hand-off note is the real one.

Run: python -B -m unittest discover -s tools/seed/tests -t . -p 'test_*.py' -v
"""
from __future__ import annotations

import fcntl
import os
import pty
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "scripts"
HA_VERSION = re.search(r"^HA_VERSION=(\S+)", (REPO_ROOT / "versions.env").read_text(encoding="utf-8"), re.M).group(1)
IMAGE = "ghcr.io/home-assistant/home-assistant:" + HA_VERSION

# Logs its arguments. For ``docker run -v SRC:/config ...`` it plays the throwaway container: its
# /config is the host directory SRC, so the wipe's find runs there (FH_STUB_NO_WIPE=1 deletes nothing,
# which is how a half-finished wipe is simulated).
STUB_DOCKER = """#!/usr/bin/env bash
printf 'docker %s\\n' "$*" >> "$FH_STUB_LOG"
if [ "$1" = "run" ]; then
  all="$*"
  src=""
  while [ $# -gt 0 ]; do
    if [ "$1" = "-v" ]; then src="${2%%:*}"; break; fi
    shift
  done
  if [ -n "$src" ]; then
    case "$all" in
      *"--entrypoint cat"*)
        # the read-only container that prints the config entries file of the stopped instance
        cat "$src/.storage/core.config_entries"
        ;;
      *"cat > /config/.storage/core.config_entries"*)
        # the container that writes the restored Google entry (its stdin is the text)
        mkdir -p "$src/.storage"
        cat > "$src/.storage/core.config_entries"
        ;;
      *"rm -rf"*)
        if [ -z "${FH_STUB_NO_WIPE:-}" ]; then
          find "$src" -mindepth 1 -maxdepth 1 ! -name custom_components -exec rm -rf {} +
        fi
        ;;
    esac
  fi
fi
exit "${FH_STUB_DOCKER_RC:-0}"
"""

# The seed stub logs its arguments, can be told to fail one command, and runs the real ``note``.
STUB_SEED = """#!/usr/bin/env bash
printf 'seed %s\\n' "$*" >> "$FH_STUB_LOG"
for word in "$@"; do
  if [ "$word" = "${FH_STUB_FAIL:-__none__}" ]; then
    echo "stub seed: $word failed" >&2
    exit 1
  fi
done
for word in "$@"; do
  if [ "$word" = "note" ]; then
    exec "$FH_STUB_PY" -B -m tools.seed "$@"
  fi
  if [ "$word" = "google-restore" ] && [ -n "${FH_STUB_RESTORE_TEXT:-}" ]; then
    printf '%s\\n' "$FH_STUB_RESTORE_TEXT"
    exit 0
  fi
done
exit 0
"""

# Replaces `date` only for the build time format, so two deploys can have two different times.
STUB_DATE = """#!/usr/bin/env bash
if [ "$1" = "+%e %b %H:%M" ] && [ -n "${FH_STUB_DATE:-}" ]; then
  printf '%s\\n' "$FH_STUB_DATE"
  exit 0
fi
exec /bin/date "$@"
"""


def write_executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class ScriptCase(unittest.TestCase):
    """A temp state dir, a stub docker and seed, and a way to run one of the scripts."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.state = root / "state"
        self.state.mkdir()
        self.bin = root / "bin"
        self.bin.mkdir()
        self.log = root / "calls.log"
        self.host_env = root / "host.env"
        self.host_env.write_text("TZ=Europe/London\nPREVIEW_HOST_IP=192.168.50.10\n", encoding="utf-8")
        write_executable(self.bin / "docker", STUB_DOCKER)
        write_executable(self.bin / "seedstub", STUB_SEED)
        write_executable(self.bin / "date", STUB_DATE)
        # The certificates exist already, so fh_ensure_certs does nothing.
        (self.state / ".ha-certs").mkdir()
        (self.state / ".ha-certs" / "fullchain.pem").write_text("x", encoding="utf-8")

    def env(self, **extra: str) -> dict[str, str]:
        base = dict(
            os.environ,
            PATH="%s:%s" % (self.bin, os.environ["PATH"]),
            FH_STATE_DIR=str(self.state),
            FH_HOST_ENV=str(self.host_env),
            FH_SEED_CMD=str(self.bin / "seedstub"),
            FH_STUB_LOG=str(self.log),
            FH_STUB_PY=sys.executable,
            PYTHONDONTWRITEBYTECODE="1",
        )
        base.pop("FH_WIPE_LOCAL", None)
        base.update(extra)
        return base

    def run_script(self, name: str, *args: str, **extra_env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(SCRIPTS / name), *args],
            cwd=REPO_ROOT,
            env=self.env(**extra_env),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=300,
        )

    def calls(self) -> list[str]:
        if not self.log.exists():
            return []
        return self.log.read_text(encoding="utf-8").splitlines()

    def position(self, calls: list[str], *needles: str) -> int:
        """Index of the first call containing every needle; fails the test when there is none."""
        for index, line in enumerate(calls):
            if all(needle in line for needle in needles):
                return index
        self.fail("no call containing %r in:\n%s" % (needles, "\n".join(calls)))

    def hold_lock(self, env_name: str):
        """Hold the environment's lock the way a running deploy would; close the handle to release."""
        directory = self.state / ".ha-locks"
        directory.mkdir(exist_ok=True)
        handle = open(directory / ("%s.lock" % env_name), "w")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.addCleanup(handle.close)
        return handle

    def populate(self, env_name: str, extras: Optional[list[str]] = None) -> Path:
        """Fill .ha-ENV with what a used instance holds, including what could resurrect old data."""
        config = self.state / (".ha-%s" % env_name)
        for relative in [
            ".storage/auth",
            "family_hub_backups/chores.json",
            "home-assistant_v2.db",
            "home-assistant.log",
            "configuration.yaml",
            ".hidden-file",
            "custom_components/family_hub/x",
            *(extras or []),
        ]:
            target = config / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("old", encoding="utf-8")
        return config

    def run_in_terminal(self, name: str, answer: str, *args: str) -> subprocess.CompletedProcess:
        """Run a script with a real terminal as stdin and type ``answer`` at its prompt."""
        master, slave = pty.openpty()
        try:
            proc = subprocess.Popen(
                [str(SCRIPTS / name), *args],
                cwd=REPO_ROOT,
                env=self.env(),
                stdin=slave,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        finally:
            os.close(slave)
        try:
            os.write(master, (answer + "\n").encode("utf-8"))
            out, err = proc.communicate(timeout=300)
        finally:
            os.close(master)
        return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


class ResetTests(ScriptCase):
    def test_no_terminal_and_no_yes_refuses_before_any_docker_call(self) -> None:
        result = self.run_script("reset-preview")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("refusing without --yes", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_yes_runs_down_then_wipe_then_up_then_seed_in_that_order(self) -> None:
        config = self.populate("preview")
        result = self.run_script("reset-preview", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        calls = self.calls()
        down = self.position(calls, "compose", "-p familyhub-preview", " down")
        wipe = self.position(calls, "docker run", "--rm", "-v %s:/config" % config, IMAGE, "find /config", "! -name custom_components")
        up = self.position(calls, "compose", "-p familyhub-preview", "up -d")
        seed = self.position(calls, "seed --target preview seed")
        restore = self.position(calls, "seed --target preview google-restore --stdout")
        backup = self.position(calls, "seed --target preview backup-calendars")
        self.assertLess(backup, down)
        self.assertLess(down, wipe)
        self.assertLess(wipe, restore)
        self.assertLess(restore, up)
        self.assertLess(up, seed)
        self.assertEqual(len(calls), 6, calls)
        self.assertIn("-f dev/compose.yaml -f dev/compose.preview.yaml", calls[down])
        self.assertIn(
            "Preview is back to the starting week. She may need to sign in again with her usual details.", result.stdout
        )
        self.assertTrue((config / "configuration.yaml").exists())
        self.assertEqual(sorted(p.name for p in config.iterdir()), ["configuration.yaml", "custom_components"])

    def test_the_wipe_run_uses_the_pinned_image_and_keeps_only_the_integration(self) -> None:
        self.populate("preview")
        self.run_script("reset-preview", "--yes")
        wipe = [line for line in self.calls() if line.startswith("docker run")]
        self.assertEqual(len(wipe), 1)
        self.assertIn("--entrypoint sh", wipe[0])
        self.assertIn("-mindepth 1 -maxdepth 1 ! -name custom_components -exec rm -rf {} +", wipe[0])

    def test_a_local_wipe_leaves_only_the_integration_and_the_template_config_comes_back(self) -> None:
        config = self.populate("preview")
        result = self.run_script("reset-preview", "--yes", FH_WIPE_LOCAL="1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(sorted(p.name for p in config.iterdir()), ["configuration.yaml", "custom_components"])
        self.assertEqual((config / "custom_components" / "family_hub" / "x").read_text(encoding="utf-8"), "old")
        template = (REPO_ROOT / "dev" / "config-template" / "configuration.yaml").read_text(encoding="utf-8")
        self.assertEqual((config / "configuration.yaml").read_text(encoding="utf-8"), template)
        self.assertFalse(any(line.startswith("docker run") for line in self.calls()))

    def test_a_wipe_that_leaves_old_data_stops_before_the_restart_and_the_seed(self) -> None:
        # The stub container deletes nothing, so .storage and family_hub_backups survive the "wipe".
        self.populate("preview")
        result = self.run_script("reset-preview", "--yes", FH_STUB_NO_WIPE="1")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(".storage", result.stderr)
        self.assertIn("family_hub_backups", result.stderr)
        calls = self.calls()
        self.assertTrue(any(" down" in line for line in calls))
        self.assertFalse(any("up -d" in line for line in calls), calls)
        self.assertFalse(any(line.startswith("seed") and "backup-calendars" not in line for line in calls), calls)
        self.assertNotIn("back to the starting week", result.stdout)

    def test_a_surviving_backup_alone_is_enough_to_stop(self) -> None:
        config = self.state / ".ha-preview"
        (config / "family_hub_backups").mkdir(parents=True)
        (config / "family_hub_backups" / "chores.json").write_text("old", encoding="utf-8")
        result = self.run_script("reset-preview", "--yes", FH_STUB_NO_WIPE="1")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(any(line.startswith("seed") and "backup-calendars" not in line for line in self.calls()))

    def test_dev_reset_does_the_same_on_dev(self) -> None:
        config = self.populate("dev")
        result = self.run_script("dev-reset", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        calls = self.calls()
        down = self.position(calls, "compose", "-p familyhub-dev", " down")
        wipe = self.position(calls, "docker run", "-v %s:/config" % config, IMAGE)
        up = self.position(calls, "compose", "-p familyhub-dev", "up -d")
        seed = self.position(calls, "seed --target dev seed")
        self.assertTrue(down < wipe < up < seed, calls)
        self.assertIn("-f dev/compose.yaml -f dev/compose.dev.yaml", calls[down])
        self.assertIn("Dev is back to the starting week.", result.stdout)

    def test_dev_reset_without_yes_and_without_a_terminal_refuses(self) -> None:
        result = self.run_script("dev-reset")
        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing without --yes", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_the_typed_word_is_asked_for_and_accepted(self) -> None:
        self.populate("preview")
        result = self.run_in_terminal("reset-preview", "PREVIEW")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("This will erase all Preview data and re-seed it. Type PREVIEW to continue:", result.stderr + result.stdout)
        self.assertTrue(any(line.startswith("seed") for line in self.calls()))

    def test_anything_but_the_exact_word_stops_everything(self) -> None:
        for wrong in ("preview", "yes", "", "DEV", "PREVIEW now"):
            with self.subTest(answer=wrong):
                self.log.unlink(missing_ok=True)
                result = self.run_in_terminal("reset-preview", wrong)
                self.assertEqual(result.returncode, 1, wrong)
                self.assertEqual(self.calls(), [])
                self.assertIn("Type PREVIEW to continue:", result.stderr + result.stdout)

    def test_dev_asks_for_dev(self) -> None:
        self.populate("dev")
        result = self.run_in_terminal("dev-reset", "DEV")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("This will erase all Dev data and re-seed it. Type DEV to continue:", result.stderr + result.stdout)
        wrong = self.run_in_terminal("dev-reset", "PREVIEW")
        self.assertEqual(wrong.returncode, 1)

    def test_a_reset_while_another_operation_holds_the_lock_changes_nothing(self) -> None:
        self.populate("preview")
        self.hold_lock("preview")
        result = self.run_script("reset-preview", "--yes")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Preview is busy", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertTrue((self.state / ".ha-preview" / ".storage" / "auth").exists())


class GoogleResetTests(ScriptCase):
    """D-10: a reset saves the Google entry of the stopped instance, wipes, and writes it back before the start."""

    RESTORED = '{"key": "core.config_entries", "data": {"entries": ["the google entry"]}}'

    def test_the_sign_in_is_saved_before_the_wipe_and_written_back_before_the_start(self) -> None:
        config = self.populate("preview", [".storage/core.config_entries"])
        result = self.run_script("reset-preview", "--yes", FH_STUB_RESTORE_TEXT=self.RESTORED)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        calls = self.calls()
        down = self.position(calls, " down")
        read = self.position(calls, "docker run", "--entrypoint cat", "-v %s:/config:ro" % config, "/config/.storage/core.config_entries")
        save = self.position(calls, "seed --target preview google-save --stdin")
        wipe = self.position(calls, "docker run", "rm -rf")
        restore = self.position(calls, "seed --target preview google-restore --stdout")
        write = self.position(calls, "docker run", "-i", "-v %s:/config" % config, "cat > /config/.storage/core.config_entries")
        up = self.position(calls, "up -d")
        seed = self.position(calls, "seed --target preview seed")
        # the read and the save run on the two ends of one pipe, so their log order is not fixed
        self.assertLess(down, min(read, save))
        self.assertLess(max(read, save), wipe)
        self.assertLess(wipe, restore)
        self.assertLess(restore, write)
        self.assertLess(write, up)
        self.assertLess(up, seed)
        written = (config / ".storage" / "core.config_entries").read_text(encoding="utf-8")
        self.assertEqual(written, self.RESTORED + "\n")
        self.assertEqual(sorted(p.name for p in config.iterdir()), [".storage", "configuration.yaml", "custom_components"])

    def test_a_failed_save_stops_before_anything_is_wiped(self) -> None:
        config = self.populate("preview", [".storage/core.config_entries"])
        result = self.run_script("reset-preview", "--yes", FH_STUB_FAIL="google-save")
        self.assertNotEqual(result.returncode, 0)
        calls = self.calls()
        self.assertFalse(any("rm -rf" in line for line in calls), calls)
        self.assertFalse(any("up -d" in line for line in calls), calls)
        self.assertFalse(any(line.startswith("seed") and line.endswith(" seed") for line in calls), calls)
        self.assertTrue((config / ".storage" / "auth").exists(), "nothing was erased")

    def test_a_failed_restore_stops_before_the_start(self) -> None:
        self.populate("preview", [".storage/core.config_entries"])
        result = self.run_script("reset-preview", "--yes", FH_STUB_FAIL="google-restore")
        self.assertNotEqual(result.returncode, 0)
        calls = self.calls()
        self.assertFalse(any("up -d" in line for line in calls), calls)
        self.assertFalse(any(line.startswith("seed") and line.endswith(" seed") for line in calls), calls)

    def test_with_nothing_saved_no_entry_is_written(self) -> None:
        config = self.populate("preview", [".storage/core.config_entries"])
        result = self.run_script("reset-preview", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse(any("cat > /config/.storage" in line for line in self.calls()))
        self.assertFalse((config / ".storage").exists())

    def test_an_instance_that_never_had_a_google_entry_file_skips_the_save(self) -> None:
        self.populate("preview")
        result = self.run_script("reset-preview", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        calls = self.calls()
        self.assertFalse(any("google-save" in line for line in calls), calls)
        self.assertFalse(any("--entrypoint cat" in line for line in calls), calls)


class DeployTests(ScriptCase):
    def old_copy(self) -> Path:
        live = self.state / ".ha-preview" / "custom_components" / "family_hub"
        live.mkdir(parents=True)
        (live / "OLD").write_text("previous", encoding="utf-8")
        return live

    def test_a_deploy_runs_every_step_in_order_and_swaps_the_copy(self) -> None:
        live = self.old_copy()
        result = self.run_script(
            "deploy-preview", "HEAD", "--what", "Chores show stars.", "--view", "Chores", "--tap", "the + button"
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        calls = self.calls()
        stop = self.position(calls, "compose", "-p familyhub-preview", " stop")
        up = self.position(calls, "compose", "-p familyhub-preview", "up -d")
        seed = self.position(calls, "seed --target preview seed")
        served = self.position(calls, "seed --target preview verify-served --expect Preview")
        note = self.position(calls, "seed --target preview note --stamp=Preview")
        backup = self.position(calls, "seed --target preview backup-calendars")
        self.assertTrue(backup < stop < up < seed < served < note, calls)
        self.assertEqual(len(calls), 6, calls)
        # the new copy is live, stamped, and the old one is gone only now
        self.assertTrue((live / "manifest.json").exists())
        self.assertFalse((live / "OLD").exists())
        self.assertEqual([p.name for p in self.state.glob(".ha-deploy.*")], [])
        card = (live / "card" / "family-week-calendar-card.js").read_text(encoding="utf-8")
        for token in ("__FH_BUILD_ENV__", "__FH_BUILD_VERSION__", "__FH_BUILD_TIME__"):
            self.assertNotIn(token, card)
        stamp = calls[served].split("--expect ", 1)[1]
        self.assertRegex(stamp, r"^Preview \u00b7 \S+\+[0-9a-f]{7} \u00b7 [1-9][0-9]? [A-Z][a-z]{2} [0-2][0-9]:[0-5][0-9]$")
        self.assertIn('"%s".' % stamp, result.stdout)
        # the ready line is printed once, after the served check, followed by what she needs to know
        self.assertEqual(result.stdout.count("Preview is updated and ready for you to try."), 1)
        self.assertIn("What changed:  Chores show stars.", result.stdout)
        self.assertIn("Where to look: Open Family Hub PREVIEW, tap Chores, then the + button.", result.stdout)
        note_lines = ("Preview is updated" + result.stdout.split("Preview is updated", 1)[1]).splitlines()
        self.assertTrue(all(len(line) <= 72 for line in note_lines), note_lines)

    def test_without_notes_the_deploy_still_succeeds_and_the_note_says_so(self) -> None:
        result = self.run_script("deploy-preview", "HEAD")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("What changed:  (no note was given - tell her what changed yourself)", result.stdout)
        self.assertIn("Where to look: Open Family Hub PREVIEW.", result.stdout)
        self.assertIn("(no screen was given - tell her where to tap yourself)", result.stdout)

    def test_an_unknown_ref_fails_before_preview_is_touched(self) -> None:
        live = self.old_copy()
        result = self.run_script("deploy-preview", "no-such-branch-anywhere")
        self.assertEqual(result.returncode, 1)
        self.assertIn("deploy-preview failed at step 3", result.stderr)
        self.assertNotIn("ready for you to try", result.stdout)
        self.assertEqual(self.calls(), ["seed --target preview backup-calendars"])
        self.assertEqual((live / "OLD").read_text(encoding="utf-8"), "previous")
        self.assertEqual([p.name for p in self.state.glob(".ha-deploy.*")], [])

    def test_a_failed_served_check_never_says_ready_and_keeps_the_previous_copy(self) -> None:
        live = self.old_copy()
        result = self.run_script("deploy-preview", "HEAD", "--what", "x", FH_STUB_FAIL="verify-served")
        self.assertEqual(result.returncode, 1)
        self.assertIn("deploy-preview failed at step 7 (checking that Preview serves the new cards)", result.stderr)
        self.assertIn("NEW copy", result.stderr)
        self.assertNotIn("ready for you to try", result.stdout + result.stderr)
        self.assertFalse(any("note" in line for line in self.calls() if line.startswith("seed")))
        kept = list(self.state.glob(".ha-deploy.*/previous/OLD"))
        self.assertEqual(len(kept), 1, "the previous copy must be kept for a rollback")
        self.assertTrue((live / "manifest.json").exists())

    def test_a_failure_before_the_swap_restarts_the_previous_copy(self) -> None:
        # A file where the integration's parent directory should be makes the swap fail after the stop.
        config = self.state / ".ha-preview"
        config.mkdir()
        (config / "custom_components").write_text("not a directory", encoding="utf-8")
        result = self.run_script("deploy-preview", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("deploy-preview failed at step 5", result.stderr)
        self.assertIn("previous copy is still the live one", result.stderr)
        calls = self.calls()
        self.assertEqual([c.split("compose", 1)[1].split()[-1] for c in calls if "compose" in c], ["stop", "-d"])
        self.assertEqual([line for line in calls if line.startswith("seed")], ["seed --target preview backup-calendars"])
        self.assertNotIn("ready for you to try", result.stdout)

    def test_a_deploy_while_another_operation_holds_the_lock_changes_nothing(self) -> None:
        live = self.old_copy()
        self.hold_lock("preview")
        result = self.run_script("deploy-preview", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Preview is busy", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertTrue((live / "OLD").exists())

    def test_deploying_the_same_ref_twice_gives_the_same_version_and_hash_and_a_newer_time(self) -> None:
        first = self.run_script("deploy-preview", "HEAD", FH_STUB_DATE="4 Nov 10:00")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_script("deploy-preview", "HEAD", FH_STUB_DATE="4 Nov 10:05")
        self.assertEqual(second.returncode, 0, second.stderr)
        stamps = [line.split("--expect ", 1)[1] for line in self.calls() if "verify-served" in line]
        self.assertEqual(len(stamps), 2)
        (env1, version1, time1), (env2, version2, time2) = (s.split(" \u00b7 ") for s in stamps)
        self.assertEqual((env1, version1), (env2, version2))
        self.assertEqual((time1, time2), ("4 Nov 10:00", "4 Nov 10:05"))
        card = (self.state / ".ha-preview/custom_components/family_hub/card/family-week-calendar-card.js").read_text(encoding="utf-8")
        self.assertIn('deployed: "4 Nov 10:05"', card)
        self.assertEqual([p.name for p in self.state.glob(".ha-deploy.*")], [])

    def test_preview_down_only_stops(self) -> None:
        result = self.run_script("preview-down")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Preview is stopped. Start it again with scripts/deploy-preview <branch> or scripts/reset-preview.", result.stdout)
        calls = self.calls()
        self.assertEqual(len(calls), 1)
        self.assertIn("-p familyhub-preview", calls[0])
        self.assertTrue(calls[0].endswith(" stop"))


class RefreshTests(ScriptCase):
    def test_a_refresh_waits_then_refreshes_and_never_stops_or_wipes_anything(self) -> None:
        config = self.populate("preview")
        result = self.run_script("refresh-preview")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        calls = self.calls()
        wait = self.position(calls, "seed --target preview", "--timeout 300", " wait")
        refresh = self.position(calls, "seed --target preview refresh")
        backup = self.position(calls, "seed --target preview backup-calendars")
        self.assertLess(wait, backup)
        self.assertLess(backup, refresh)
        self.assertEqual(len(calls), 3, calls)
        self.assertFalse(any(line.startswith("docker") for line in calls), calls)
        self.assertRegex(result.stdout.strip().splitlines()[-1], r"^Preview refreshed: \d{4}-\d{2}-\d{2}$")
        # nothing of hers was touched on disk
        self.assertTrue((config / ".storage" / "auth").exists())
        self.assertTrue((config / "family_hub_backups" / "chores.json").exists())

    def test_the_yes_flag_is_accepted_for_symmetry_and_nothing_is_asked(self) -> None:
        result = self.run_script("refresh-preview", "--yes")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 3)

    def test_when_preview_is_not_running_it_says_so_and_does_not_refresh(self) -> None:
        result = self.run_script("refresh-preview", FH_STUB_FAIL="wait")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Preview is not running", result.stderr)
        self.assertIn("is WSL/Docker up?", result.stderr)
        calls = self.calls()
        self.assertEqual(len(calls), 1, calls)
        self.assertNotIn("refresh", calls[0])
        self.assertNotIn("Preview refreshed", result.stdout)

    def test_a_failed_refresh_exits_non_zero_without_the_success_line(self) -> None:
        result = self.run_script("refresh-preview", FH_STUB_FAIL="refresh")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Preview refreshed", result.stdout)

    def test_a_refresh_while_another_operation_holds_the_lock_changes_nothing(self) -> None:
        self.hold_lock("preview")
        result = self.run_script("refresh-preview")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Preview is busy", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_the_script_has_no_path_to_a_stop_or_a_wipe(self) -> None:
        text = (SCRIPTS / "refresh-preview").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"compose (preview |\$ENV )?down|fh_wipe", text))
        self.assertIn("fh_backup_calendars preview", text)

    def test_every_destructive_script_calls_the_calendar_backup_once(self) -> None:
        # D-08: the definition lives in lib.sh; fh_reset_env, deploy-preview and refresh-preview each call it.
        lib = (SCRIPTS / "lib.sh").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^fh_backup_calendars\(\)", lib, re.M)), 1)
        reset = lib[lib.index("fh_reset_env()") :]
        self.assertEqual(len(re.findall(r"^\s*fh_backup_calendars ", reset, re.M)), 1)
        for name in ("deploy-preview", "refresh-preview"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"^\s*fh_backup_calendars ", text, re.M)), 1, name)


class BackupHardStopTests(ScriptCase):
    """D-08, D-30, PREV-03: when any chosen calendar's backup fails, nothing is stopped, wiped or changed."""

    BACKUP = "seed --target preview backup-calendars"

    def stops_hard(self, result, expected_calls: list) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        calls = self.calls()
        self.assertEqual(calls, expected_calls)
        self.assertFalse(any(line.startswith("docker") for line in calls), "no stop, down, wipe or up")
        self.assertFalse(any("refresh" in line or line.endswith(" seed") for line in calls), "no refresh or seed after it")

    def test_a_failed_backup_stops_deploy_preview_before_anything_is_touched(self) -> None:
        live = self.state / ".ha-preview" / "custom_components" / "family_hub"
        live.mkdir(parents=True)
        (live / "OLD").write_text("previous", encoding="utf-8")
        result = self.run_script("deploy-preview", "HEAD", FH_STUB_FAIL="backup-calendars")
        self.stops_hard(result, [self.BACKUP])
        self.assertTrue((live / "OLD").exists())
        self.assertEqual([p.name for p in self.state.glob(".ha-deploy.*")], [], "nothing was even exported")
        self.assertNotIn("ready for you to try", result.stdout)

    def test_a_failed_backup_stops_reset_preview_before_the_stop_and_the_wipe(self) -> None:
        config = self.populate("preview")
        result = self.run_script("reset-preview", "--yes", FH_STUB_FAIL="backup-calendars")
        self.stops_hard(result, [self.BACKUP])
        self.assertTrue((config / ".storage" / "auth").exists())
        self.assertTrue((config / "family_hub_backups" / "chores.json").exists())

    def test_a_failed_backup_stops_dev_reset_before_the_stop_and_the_wipe(self) -> None:
        config = self.populate("dev")
        result = self.run_script("dev-reset", "--yes", FH_STUB_FAIL="backup-calendars")
        self.stops_hard(result, ["seed --target dev backup-calendars"])
        self.assertTrue((config / ".storage" / "auth").exists())

    def test_a_failed_backup_stops_refresh_preview_before_the_refresh(self) -> None:
        self.populate("preview")
        result = self.run_script("refresh-preview", FH_STUB_FAIL="backup-calendars")
        self.stops_hard(result, ["seed --target preview --timeout 300 wait", self.BACKUP])
        self.assertNotIn("Preview refreshed", result.stdout)

    def test_the_backup_is_the_first_call_of_every_destructive_script(self) -> None:
        self.populate("preview")
        for name, args in (("reset-preview", ("--yes",)), ("deploy-preview", ("HEAD",))):
            with self.subTest(script=name):
                self.log.unlink(missing_ok=True)
                result = self.run_script(name, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.calls()[0], self.BACKUP)

    def test_a_calendar_backup_runs_with_the_secrets_and_backups_directories_mounted(self) -> None:
        text = (SCRIPTS / "lib.sh").read_text(encoding="utf-8")
        self.assertIn("$FH_STATE_DIR/.ha-backups:/work/dev/.ha-backups", text)
        self.assertIn('chmod 700 "$FH_STATE_DIR/.ha-backups"', text)


class ComposeStateTests(ScriptCase):
    def test_state_dir_and_host_env_can_be_redirected_for_every_helper(self) -> None:
        text = (SCRIPTS / "lib.sh").read_text(encoding="utf-8")
        self.assertNotIn('"$FH_ROOT/dev/.ha-', text.replace('"$FH_ROOT/dev/.ha-secrets', ""))
        self.assertIn("FH_STATE_DIR", text)


if __name__ == "__main__":
    unittest.main()
