#Requires -RunAsAdministrator
<#
.SYNOPSIS
    One-time Windows side of the Family Hub laptop setup (Dev and Preview run in WSL2 + Docker Engine).

.DESCRIPTION
    Run this once in an elevated PowerShell (Run as administrator), after the Ubuntu side is set up
    and scripts/make-certs has created dev/.ha-certs. Running it again is safe: every step replaces
    what it made before.

    1. %UserProfile%\.wslconfig gets networkingMode=mirrored under [wsl2]. A dated copy of the old
       file is kept next to it first.
    2. One Hyper-V firewall rule, FamilyHubPreview, lets the home network reach TCP port 8124
       (Preview) on the WSL virtual machine. Nothing else is opened: Dev (port 8130) stays on this
       laptop only.
    3. Three scheduled tasks for the current user:
         "FamilyHub WSL keep-alive"     at logon: keeps WSL (and so Docker and Preview) running
         "FamilyHub refresh at logon"   at logon, after 2 minutes: scripts/refresh-preview --yes
         "FamilyHub refresh daily"      every day at -DailyTime, run late if the laptop was off
    4. The local root certificate (ca.crt only, never a key) is added to this user's trusted roots,
       so the Windows browser trusts https://127.0.0.1:8130 and https://<reserved-ip>:8124.
    5. The Wi-Fi network profile is reported, and the next steps are printed.

    Preview is only up while this Windows user is logged in and the laptop is awake (D-03).

.PARAMETER Distro
    The WSL distribution name (see: wsl -l -v). Default "Ubuntu".

.PARAMETER RepoPath
    Where the repository is inside WSL. Default "~/HA-Family-Hub". Never a /mnt path.

.PARAMETER DailyTime
    Time of the daily refresh, 24-hour HH:mm. Default "05:30".

.PARAMETER RemoteSubnet
    Optional. Limits the firewall rule to the home network, for example 192.168.50.0/24.

.PARAMETER SkipCaImport
    Do not import ca.crt into the Windows trusted root store.
#>
[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu",
    [string]$RepoPath = "~/HA-Family-Hub",
    [string]$DailyTime = "05:30",
    [string]$RemoteSubnet = "",
    [switch]$SkipCaImport
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Text) {
    Write-Host ""
    Write-Host "==> $Text"
}

# ---------------------------------------------------------------------------------------------
# 1. Mirrored networking in .wslconfig
# ---------------------------------------------------------------------------------------------
Write-Step "Mirrored networking in .wslconfig"

$wslConfigPath = Join-Path $env:UserProfile ".wslconfig"
$desiredLine = "networkingMode=mirrored"
$oldLines = @()
if (Test-Path -LiteralPath $wslConfigPath) {
    $oldLines = @(Get-Content -LiteralPath $wslConfigPath)
}

$newLines = New-Object System.Collections.Generic.List[string]
$inWsl2 = $false
$sawWsl2 = $false
$handled = $false
foreach ($line in $oldLines) {
    if ($line -match '^\s*\[(.+?)\]\s*$') {
        if ($inWsl2 -and -not $handled) {
            $newLines.Add($desiredLine)
            $handled = $true
        }
        $inWsl2 = ($Matches[1].Trim() -ieq "wsl2")
        if ($inWsl2) { $sawWsl2 = $true }
        $newLines.Add($line)
        continue
    }
    if ($inWsl2 -and $line -match '^\s*networkingMode\s*=') {
        if (-not $handled) {
            $newLines.Add($desiredLine)
            $handled = $true
        }
        continue
    }
    $newLines.Add($line)
}
if (-not $handled) {
    if ($sawWsl2) {
        $newLines.Add($desiredLine)
    } else {
        if ($newLines.Count -gt 0) { $newLines.Add("") }
        $newLines.Add("[wsl2]")
        $newLines.Add($desiredLine)
    }
}

$unchanged = ($oldLines.Count -eq $newLines.Count)
if ($unchanged) {
    for ($i = 0; $i -lt $oldLines.Count; $i++) {
        if ($oldLines[$i] -cne $newLines[$i]) { $unchanged = $false; break }
    }
}
if ($unchanged) {
    Write-Host "Already set: $wslConfigPath has $desiredLine under [wsl2]."
} else {
    if (Test-Path -LiteralPath $wslConfigPath) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backupPath = "$wslConfigPath.familyhub-$stamp"
        Copy-Item -LiteralPath $wslConfigPath -Destination $backupPath
        Write-Host "Kept a copy of the old file: $backupPath"
    }
    [System.IO.File]::WriteAllLines($wslConfigPath, $newLines.ToArray(), (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "Wrote $desiredLine to $wslConfigPath. It takes effect after: wsl --shutdown"
}

# ---------------------------------------------------------------------------------------------
# 2. Hyper-V firewall rule for Preview (TCP 8124 only)
# ---------------------------------------------------------------------------------------------
Write-Step "Hyper-V firewall rule FamilyHubPreview (TCP 8124)"

if (-not (Get-Command New-NetFirewallHyperVRule -ErrorAction SilentlyContinue)) {
    throw "New-NetFirewallHyperVRule is not available. This needs Windows 11 22H2 or later with a current WSL (wsl --version)."
}
Remove-NetFirewallHyperVRule -Name "FamilyHubPreview" -ErrorAction SilentlyContinue
$extraRuleParams = @{}
if ($RemoteSubnet) {
    $extraRuleParams["RemoteAddresses"] = $RemoteSubnet
}
New-NetFirewallHyperVRule -Name "FamilyHubPreview" -DisplayName "Family Hub Preview" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 8124 @extraRuleParams | Out-Null
if ($RemoteSubnet) {
    Write-Host "Rule created: the home network $RemoteSubnet can reach port 8124 on WSL."
} else {
    Write-Host "Rule created: any network this laptop joins can reach port 8124 on WSL while Preview runs. Run scripts/preview-down before leaving home, or re-run this script with -RemoteSubnet."
}

# ---------------------------------------------------------------------------------------------
# 3. Scheduled tasks (current user, only while logged on)
# ---------------------------------------------------------------------------------------------
Write-Step "Scheduled tasks"

$userId = "$env:UserDomain\$env:UserName"
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited
$refreshArgs = '-d {0} -e bash -lc "{1}/scripts/refresh-preview --yes"' -f $Distro, $RepoPath

# Keep WSL alive: WSL stops the distribution when no Windows process holds it open, and a service
# inside Linux does not count. No time limit, restart if it ever stops.
$keepAliveAction = New-ScheduledTaskAction -Execute "wsl.exe" -Argument ("-d {0} -e sleep infinity" -f $Distro)
$keepAliveTrigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
$keepAliveSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "FamilyHub WSL keep-alive" -Action $keepAliveAction -Trigger $keepAliveTrigger -Settings $keepAliveSettings -Principal $principal -Description "Keeps WSL running so Family Hub Preview stays up while you are logged in." -Force | Out-Null
Write-Host "Registered: FamilyHub WSL keep-alive (at logon)"

# Refresh at logon, after Docker and Home Assistant have had time to start.
$logonAction = New-ScheduledTaskAction -Execute "wsl.exe" -Argument $refreshArgs
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
$logonTrigger.Delay = "PT2M"
$refreshSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "FamilyHub refresh at logon" -Action $logonAction -Trigger $logonTrigger -Settings $refreshSettings -Principal $principal -Description "Tops up Family Hub Preview two minutes after you log on." -Force | Out-Null
Write-Host "Registered: FamilyHub refresh at logon (2 minute delay)"

# Daily refresh; StartWhenAvailable runs it as soon as possible when the laptop was off at that time.
$dailyAction = New-ScheduledTaskAction -Execute "wsl.exe" -Argument $refreshArgs
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At $DailyTime
Register-ScheduledTask -TaskName "FamilyHub refresh daily" -Action $dailyAction -Trigger $dailyTrigger -Settings $refreshSettings -Principal $principal -Description "Tops up Family Hub Preview every day." -Force | Out-Null
Write-Host "Registered: FamilyHub refresh daily (at $DailyTime, run late if missed)"

# ---------------------------------------------------------------------------------------------
# 4. Trust the local root certificate (ca.crt only)
# ---------------------------------------------------------------------------------------------
Write-Step "Local root certificate"

if ($SkipCaImport) {
    Write-Host "Skipped (-SkipCaImport)."
} else {
    $repoInWsl = $RepoPath
    if ($repoInWsl.StartsWith("~")) {
        # Not $home: that is a read-only PowerShell variable (the Windows home directory).
        $wslHome = (& wsl.exe -d $Distro -e sh -c 'printf %s "$HOME"') -join ""
        $wslHome = ($wslHome -replace "`0", "").Trim()
        if (-not $wslHome) {
            throw "Could not read the home directory of $Distro. Is the distribution name right (wsl -l -v)?"
        }
        $repoInWsl = $wslHome + $repoInWsl.Substring(1)
    }
    $caPath = '\\wsl$\{0}{1}' -f $Distro, (($repoInWsl.TrimEnd("/") + "/dev/.ha-certs/ca.crt") -replace "/", "\")
    if ((Split-Path -Leaf $caPath) -ne "ca.crt") {
        throw "Refusing to import anything but ca.crt."
    }
    if (-not (Test-Path -LiteralPath $caPath)) {
        throw "ca.crt not found at $caPath. Run scripts/make-certs inside Ubuntu first (or pass -SkipCaImport)."
    }
    $caCert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($caPath)
    $already = Get-ChildItem Cert:\CurrentUser\Root | Where-Object { $_.Thumbprint -eq $caCert.Thumbprint }
    if ($already) {
        Write-Host "Already trusted: $($caCert.Subject)"
    } else {
        Write-Host "Windows may ask you to confirm installing this certificate: answer Yes."
        Import-Certificate -FilePath $caPath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
        Write-Host "Imported ca.crt into the trusted root store of $env:UserName."
    }
}

# ---------------------------------------------------------------------------------------------
# 5. Wi-Fi profile and next steps
# ---------------------------------------------------------------------------------------------
Write-Step "Wi-Fi network profile"

$profiles = @(Get-NetConnectionProfile -ErrorAction SilentlyContinue | Where-Object { $_.InterfaceAlias -match "Wi-?Fi|Wireless" })
if ($profiles.Count -eq 0) {
    Write-Host "No Wi-Fi connection found. Connect to the home Wi-Fi and check it is a Private network."
}
foreach ($p in $profiles) {
    Write-Host ("{0}: {1} network" -f $p.Name, $p.NetworkCategory)
    if ($p.NetworkCategory -eq "Public") {
        Write-Warning ("'{0}' is a Public network, which can block her phone. If you trust it, run: Set-NetConnectionProfile -InterfaceAlias '{1}' -NetworkCategory Private" -f $p.Name, $p.InterfaceAlias)
    }
}

Write-Host ""
Write-Host "Done. Next steps:"
Write-Host "  1. In PowerShell run: wsl --shutdown   (wait 8 seconds, then open Ubuntu again)"
Write-Host "  2. Settings > Network & internet > Wi-Fi > <home network> > Random hardware addresses = Off"
Write-Host "  3. In the router, reserve this laptop's Wi-Fi address (DHCP reservation) and put it in dev/host.env as PREVIEW_HOST_IP"
Write-Host "  4. In Ubuntu run: scripts/doctor   and fix every FAIL"
