"""Tests for scripts/doctor with stubbed Windows tools.

There is no Windows, WSL or Docker daemon in the sandbox, so doctor's Windows checks are proven with
stub executables (wsl.exe, cmd.exe, powershell.exe, netsh.exe, schtasks.exe, plus docker, systemctl
and ss) at the front of PATH and a fake /proc/version (FH_DOCTOR_PROC_VERSION). Every run uses a
temporary FH_STATE_DIR and host.env, so nothing here reads or writes the real dev/ state. Stub output
is fed from files the test writes, so CRLF and NUL bytes (wsl.exe writes UTF-16) are exact.

Run: python -B -m unittest discover -s tools/seed/tests -t . -p 'test_doctor.py' -v
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCTOR = REPO_ROOT / "scripts" / "doctor"
MAKE_CERTS = REPO_ROOT / "scripts" / "make-certs"

IDS = [
    "host.wsl", "wsl.version", "wsl.mirrored", "wsl.systemd", "docker.engine", "docker.compose",
    "repo.location", "env.hostfile", "secrets.perms", "clock.skew", "ports.free", "net.ip",
    "cert.san", "fw.hyperv", "tasks.scheduled", "wifi.randommac",
]
WINDOWS_ONLY = [
    "wsl.version", "wsl.mirrored", "wsl.systemd", "clock.skew", "net.ip", "fw.hyperv",
    "tasks.scheduled", "wifi.randommac",
]
RESERVED_IP = "192.168.50.10"
WSL_KERNEL = "Linux version 5.15.153.1-microsoft-standard-WSL2 (root@build) (gcc 11.2.0) #1 SMP"

STUBS = {
    "docker": """#!/usr/bin/env bash
case "$1" in
  info)
    printf '%s\\r\\n' "${FH_STUB_DOCKER_OS:-Ubuntu 24.04.1 LTS}"
    exit "${FH_STUB_DOCKER_INFO_RC:-0}"
    ;;
  compose) printf 'v2.40.1\\n' ;;
  ps) exit 0 ;;
esac
exit 0
""",
    "systemctl": """#!/usr/bin/env bash
echo "${FH_STUB_SYSTEMD_STATE:-running}"
""",
    "ss": """#!/usr/bin/env bash
echo "State Recv-Q Send-Q Local Address:Port Peer Address:Port Process"
[ -n "${FH_STUB_SS_FILE:-}" ] && cat "$FH_STUB_SS_FILE"
exit 0
""",
    "wsl.exe": """#!/usr/bin/env bash
if [ "$1" = "--version" ]; then
  cat "$FH_STUB_WSL_VERSION_FILE"
fi
""",
    "cmd.exe": """#!/usr/bin/env bash
# cmd.exe /c type %UserProfile%\\.wslconfig
[ -f "$FH_STUB_WSLCONFIG_FILE" ] && cat "$FH_STUB_WSLCONFIG_FILE"
exit 0
""",
    "powershell.exe": """#!/usr/bin/env bash
all="$*"
case "$all" in
  *UnixTimeSeconds*)
    printf '%s\\r\\n' "$(( $(date -u +%s) + ${FH_STUB_CLOCK_OFFSET:-0} ))"
    ;;
  *Get-NetIPAddress*)
    cat "$FH_STUB_IPS_FILE"
    ;;
  *Get-NetFirewallHyperVRule*)
    case "${FH_STUB_HYPERV:-found}" in
      found) printf 'Name        : FamilyHubPreview\\r\\nEnabled     : True\\r\\n' ;;
      denied) printf 'Get-NetFirewallHyperVRule : Access is denied.\\r\\n' >&2; exit 1 ;;
      missing)
        printf "Get-NetFirewallHyperVRule : No MSFT_NetFirewallHyperVRule objects found with property 'Name' equal to 'FamilyHubPreview'.\\r\\n" >&2
        exit 1
        ;;
    esac
    ;;
esac
""",
    "netsh.exe": """#!/usr/bin/env bash
cat "$FH_STUB_NETSH_FILE"
""",
    "schtasks.exe": """#!/usr/bin/env bash
# schtasks.exe /query /tn NAME
name="$3"
case "${FH_STUB_TASKS_MISSING:-}" in
  *"$name"*) printf 'ERROR: The system cannot find the file specified.\\r\\n' >&2; exit 1 ;;
esac
printf 'TaskName    Next Run Time    Status\\r\\n%s    N/A    Ready\\r\\n' "$name"
""",
}

EXCLUDED_DEFAULT = (
    "\r\nProtocol tcp Port Exclusion Ranges\r\n\r\n"
    "Start Port    End Port\r\n----------    --------\r\n"
    "      5357        5357\r\n     50000       50059     *\r\n\r\n"
    "* - Administered port exclusions.\r\n"
)


def parse(output: str) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        m = re.match(r"^(PASS|WARN|FAIL|SKIP|INFO) (\S+) (.*)$", line)
        if m:
            found.setdefault(m.group(2), (m.group(1), m.group(3)))
    return found


class DoctorBase(unittest.TestCase):
    certs_dir: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._certs_tmp = tempfile.mkdtemp(prefix="fh-doctor-certs-")
        cls.certs_dir = Path(cls._certs_tmp) / ".ha-certs"
        subprocess.run(
            [str(MAKE_CERTS), "--out", str(cls.certs_dir), "--ip", RESERVED_IP],
            check=True, capture_output=True, text=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls._certs_tmp, ignore_errors=True)

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-doctor-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state = self.tmp / "state"
        self.state.mkdir()
        shutil.copytree(self.certs_dir, self.state / ".ha-certs")
        self.stubs = self.tmp / "stubs"
        self.stubs.mkdir()
        for name, body in STUBS.items():
            path = self.stubs / name
            path.write_text(body, encoding="utf-8")
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.host_env = self.tmp / "host.env"
        self.write_host_env(RESERVED_IP)
        self.files = self.tmp / "files"
        self.files.mkdir()
        self.set_proc_version(WSL_KERNEL)
        self.set_wsl_conf("[boot]\nsystemd=true\n")
        self.set_bytes("wsl_version", b"WSL version: 2.6.1.0\r\nKernel version: 6.6.87.2-1\r\n")
        self.set_bytes("wslconfig", b"[wsl2]\r\nnetworkingMode=mirrored\r\n")
        self.set_bytes("ips", f"127.0.0.1\r\n{RESERVED_IP}\r\n".encode())
        self.set_bytes("netsh", EXCLUDED_DEFAULT.encode())
        self.env_extra: dict[str, str] = {}

    # fixtures -----------------------------------------------------------------------------
    def write_host_env(self, ip: Optional[str]) -> None:
        lines = ["TZ=Europe/London"]
        if ip is not None:
            lines.append(f"PREVIEW_HOST_IP={ip}")
        self.host_env.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def set_bytes(self, name: str, data: bytes) -> None:
        (self.tmp / "files" / name).write_bytes(data)

    def set_proc_version(self, text: str) -> None:
        (self.tmp / "proc_version").write_text(text + "\n", encoding="utf-8")

    def set_wsl_conf(self, text: str) -> None:
        (self.tmp / "wsl.conf").write_text(text, encoding="utf-8")

    # running ------------------------------------------------------------------------------
    def run_doctor(self, fake_wsl: bool = True, use_stubs: bool = True) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("FH_", "PREVIEW_"))}
        env["FH_STATE_DIR"] = str(self.state)
        env["FH_HOST_ENV"] = str(self.host_env)
        env["TZ"] = "UTC"
        if use_stubs:
            env["PATH"] = f"{self.stubs}{os.pathsep}{env.get('PATH', '')}"
        if fake_wsl:
            env["FH_DOCTOR_PROC_VERSION"] = str(self.tmp / "proc_version")
            env["FH_DOCTOR_WSL_CONF"] = str(self.tmp / "wsl.conf")
            env["FH_STUB_WSL_VERSION_FILE"] = str(self.files / "wsl_version")
            env["FH_STUB_WSLCONFIG_FILE"] = str(self.files / "wslconfig")
            env["FH_STUB_IPS_FILE"] = str(self.files / "ips")
            env["FH_STUB_NETSH_FILE"] = str(self.files / "netsh")
        env.update(self.env_extra)
        return subprocess.run(
            ["bash", str(DOCTOR)], cwd=str(REPO_ROOT), env=env,
            capture_output=True, text=True, timeout=120,
        )

    def results(self, proc: subprocess.CompletedProcess) -> dict[str, tuple[str, str]]:
        return parse(proc.stdout)

    def assert_status(self, results: dict, check: str, status: str) -> None:
        self.assertIn(check, results, f"{check} missing from the output")
        self.assertEqual(results[check][0], status, f"{check}: {results[check]}")


class SandboxRunTests(DoctorBase):
    def test_a_plain_linux_host_skips_windows_checks_and_fails_without_a_docker_daemon(self) -> None:
        real = Path("/proc/version").read_text(errors="replace").lower() if Path("/proc/version").exists() else ""
        if "microsoft" in real and "wsl2" in real:
            self.skipTest("this test needs a host that is not WSL2")
        # A docker that cannot reach a daemon, so the answer does not depend on this machine.
        (self.stubs / "docker").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        proc = self.run_doctor(fake_wsl=False)
        counts: dict[str, int] = {}
        for line in proc.stdout.splitlines():
            m = re.match(r"^(?:PASS|WARN|FAIL|SKIP|INFO) (\S+) ", line)
            if m:
                counts[m.group(1)] = counts.get(m.group(1), 0) + 1
        for check in IDS:
            self.assertEqual(counts.get(check, 0), 1, f"{check} appears {counts.get(check, 0)} times\n{proc.stdout}")
        self.assertEqual(sorted(counts), sorted(IDS), "unexpected extra ids in the output")
        res = self.results(proc)
        for check in WINDOWS_ONLY:
            self.assert_status(res, check, "SKIP")
        self.assert_status(res, "docker.engine", "FAIL")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertRegex(proc.stdout, r"(?m)^doctor: \d+ pass, \d+ warn, [1-9]\d* fail, \d+ skip$")


class FakeWslTests(DoctorBase):
    def test_b_old_wsl_without_mirrored_networking(self) -> None:
        self.set_bytes("wsl_version", b"WSL version: 2.9.4.0\r\nKernel version: 6.6.87.2-1\r\n")
        self.set_bytes("wslconfig", b"[wsl2]\r\nmemory=8GB\r\n")
        proc = self.run_doctor()
        res = self.results(proc)
        self.assert_status(res, "wsl.version", "WARN")
        self.assertIn("2.9.4.0", res["wsl.version"][1])
        self.assert_status(res, "wsl.mirrored", "FAIL")
        self.assert_status(res, "net.ip", "PASS")
        self.assert_status(res, "clock.skew", "PASS")
        self.assert_status(res, "tasks.scheduled", "PASS")
        self.assert_status(res, "fw.hyperv", "PASS")
        self.assert_status(res, "cert.san", "PASS")
        self.assert_status(res, "secrets.perms", "PASS")
        self.assertEqual(proc.returncode, 1, proc.stdout)

    def test_clean_host_has_no_fail_and_exits_zero(self) -> None:
        proc = self.run_doctor()
        res = self.results(proc)
        for check in IDS:
            self.assertIn(check, res)
        self.assertNotRegex(proc.stdout, r"(?m)^FAIL ")
        self.assertRegex(proc.stdout, r"(?m)^doctor: \d+ pass, \d+ warn, 0 fail, \d+ skip$")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assert_status(res, "host.wsl", "INFO")
        self.assert_status(res, "wifi.randommac", "INFO")
        self.assertIn("Random hardware addresses", res["wifi.randommac"][1])
        self.assert_status(res, "wsl.version", "PASS")
        self.assert_status(res, "wsl.mirrored", "PASS")
        self.assert_status(res, "wsl.systemd", "PASS")
        self.assert_status(res, "docker.engine", "PASS")
        self.assert_status(res, "docker.compose", "PASS")
        self.assert_status(res, "ports.free", "PASS")

    def test_c_clocks_120_seconds_apart(self) -> None:
        self.env_extra["FH_STUB_CLOCK_OFFSET"] = "120"
        proc = self.run_doctor()
        res = self.results(proc)
        self.assert_status(res, "clock.skew", "FAIL")
        self.assertRegex(res["clock.skew"][1], r"differ by 1(19|20|21)s")
        self.assertEqual(proc.returncode, 1)

    def test_c_clock_behind_by_120_seconds_also_fails(self) -> None:
        self.env_extra["FH_STUB_CLOCK_OFFSET"] = "-120"
        self.assert_status(self.results(self.run_doctor()), "clock.skew", "FAIL")

    def test_d_repo_under_mnt_c_fails(self) -> None:
        self.env_extra["FH_DOCTOR_ROOT"] = "/mnt/c/Users/dev/HA-Family-Hub"
        proc = self.run_doctor()
        res = self.results(proc)
        self.assert_status(res, "repo.location", "FAIL")
        self.assertIn("/mnt/c/Users/dev/HA-Family-Hub", res["repo.location"][1])
        self.assertEqual(proc.returncode, 1)

    def test_e_crlf_and_nul_output_is_parsed(self) -> None:
        # wsl.exe writes UTF-16: every character followed by a NUL, lines ended with CR LF.
        text = "WSL version: 2.6.1.0\r\nKernel version: 6.6.87.2-1\r\n"
        self.set_bytes("wsl_version", b"".join(c.encode() + b"\x00" for c in text))
        self.set_bytes("wslconfig", b"[wsl2]\r\nnetworkingMode = Mirrored \r\n")
        self.set_bytes("ips", f"10.0.0.7\r\n{RESERVED_IP}\r\n".encode())
        res = self.results(self.run_doctor())
        self.assert_status(res, "wsl.version", "PASS")
        self.assertIn("2.6.1.0", res["wsl.version"][1])
        self.assertNotIn("\r", res["wsl.version"][1])
        self.assert_status(res, "wsl.mirrored", "PASS")
        self.assert_status(res, "net.ip", "PASS")
        self.assert_status(res, "clock.skew", "PASS")

    def test_every_output_line_is_clean_text(self) -> None:
        proc = self.run_doctor()
        self.assertNotIn("\r", proc.stdout)
        self.assertNotIn("\x00", proc.stdout)

    def test_net_ip_fails_when_reserved_ip_is_not_a_windows_address(self) -> None:
        self.set_bytes("ips", b"127.0.0.1\r\n192.168.50.77\r\n")
        res = self.results(self.run_doctor())
        self.assert_status(res, "net.ip", "FAIL")
        self.assertIn("192.168.50.77", res["net.ip"][1])

    def test_cert_san_fails_when_leaf_lacks_the_reserved_ip(self) -> None:
        self.write_host_env("192.168.50.99")
        self.set_bytes("ips", b"192.168.50.99\r\n")
        res = self.results(self.run_doctor())
        self.assert_status(res, "net.ip", "PASS")
        self.assert_status(res, "cert.san", "FAIL")
        self.assertIn("make-certs", res["cert.san"][1])

    def test_cert_san_does_not_accept_a_longer_address_with_the_same_prefix(self) -> None:
        self.write_host_env("192.168.50.1")
        self.set_bytes("ips", b"192.168.50.1\r\n")
        self.assert_status(self.results(self.run_doctor()), "cert.san", "FAIL")

    def test_ports_inside_a_windows_excluded_range_fail(self) -> None:
        self.set_bytes("netsh", EXCLUDED_DEFAULT.replace("5357        5357", "8100        8199").encode())
        res = self.results(self.run_doctor())
        self.assert_status(res, "ports.free", "FAIL")
        self.assertIn("8124", res["ports.free"][1])
        self.assertIn("8130", res["ports.free"][1])

    def test_a_port_held_by_another_program_fails_and_docker_proxy_does_not(self) -> None:
        ss_file = self.files / "ss"
        ss_file.write_text('LISTEN 0 128 127.0.0.1:8130 0.0.0.0:* users:(("python3",pid=77,fd=5))\n', encoding="utf-8")
        self.env_extra["FH_STUB_SS_FILE"] = str(ss_file)
        res = self.results(self.run_doctor())
        self.assert_status(res, "ports.free", "FAIL")
        self.assertIn("python3", res["ports.free"][1])
        ss_file.write_text('LISTEN 0 4096 0.0.0.0:8124 0.0.0.0:* users:(("docker-proxy",pid=88,fd=4))\n', encoding="utf-8")
        self.assert_status(self.results(self.run_doctor()), "ports.free", "PASS")

    def test_docker_desktop_is_a_fail(self) -> None:
        self.env_extra["FH_STUB_DOCKER_OS"] = "Docker Desktop"
        self.assert_status(self.results(self.run_doctor()), "docker.engine", "FAIL")

    def test_stopped_docker_daemon_is_a_fail(self) -> None:
        self.env_extra["FH_STUB_DOCKER_INFO_RC"] = "1"
        self.assert_status(self.results(self.run_doctor()), "docker.engine", "FAIL")

    def test_hyperv_rule_states(self) -> None:
        self.env_extra["FH_STUB_HYPERV"] = "denied"
        res = self.results(self.run_doctor())
        self.assert_status(res, "fw.hyperv", "WARN")
        self.assertIn("Get-NetFirewallHyperVRule -Name FamilyHubPreview", res["fw.hyperv"][1])
        self.env_extra["FH_STUB_HYPERV"] = "missing"
        self.assert_status(self.results(self.run_doctor()), "fw.hyperv", "FAIL")

    def test_missing_scheduled_task_is_a_warn_that_names_it(self) -> None:
        self.env_extra["FH_STUB_TASKS_MISSING"] = "FamilyHub refresh daily"
        res = self.results(self.run_doctor())
        self.assert_status(res, "tasks.scheduled", "WARN")
        self.assertIn("FamilyHub refresh daily", res["tasks.scheduled"][1])
        self.assertNotIn("FamilyHub WSL keep-alive", res["tasks.scheduled"][1])

    def test_systemd_off_is_a_fail(self) -> None:
        self.set_wsl_conf("[boot]\n")
        self.assert_status(self.results(self.run_doctor()), "wsl.systemd", "FAIL")

    def test_loose_secret_permissions_fail(self) -> None:
        secrets = self.state / ".ha-secrets"
        secrets.mkdir(mode=0o700)
        secrets.chmod(0o700)
        token = secrets / "credentials-dev.json"
        token.write_text("{}", encoding="utf-8")
        token.chmod(0o644)
        res = self.results(self.run_doctor())
        self.assert_status(res, "secrets.perms", "FAIL")
        self.assertIn("credentials-dev.json", res["secrets.perms"][1])
        token.chmod(0o600)
        self.assert_status(self.results(self.run_doctor()), "secrets.perms", "PASS")

    def test_missing_host_file_is_a_fail_not_an_abort(self) -> None:
        self.host_env.unlink()
        proc = self.run_doctor()
        res = self.results(proc)
        self.assert_status(res, "env.hostfile", "FAIL")
        for check in IDS:
            self.assertIn(check, res)
        self.assertEqual(proc.returncode, 1)

    def test_host_file_without_ip_is_a_fail(self) -> None:
        self.write_host_env(None)
        res = self.results(self.run_doctor())
        self.assert_status(res, "env.hostfile", "FAIL")
        self.assertIn("PREVIEW_HOST_IP", res["env.hostfile"][1])


if __name__ == "__main__":
    unittest.main()
