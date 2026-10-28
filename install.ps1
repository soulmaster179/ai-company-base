# Cài (hoặc gỡ) bộ công ty AI vào thư mục Claude dùng chung: %USERPROFILE%\.claude
#   Cài / cập nhật:  powershell -ExecutionPolicy Bypass -File install.ps1
#   Gỡ:              powershell -ExecutionPolicy Bypass -File install.ps1 -Uninstall
param(
    [switch]$Uninstall,
    [string]$ClaudeHome
)

$ErrorActionPreference = 'Stop'
$src = Join-Path $PSScriptRoot '.claude'
$dst = if ($ClaudeHome) { $ClaudeHome } else { Join-Path $HOME '.claude' }
$memoryRoot = Join-Path $dst 'ai-company-base'
$autosaveScript = Join-Path $memoryRoot 'scripts\session_autosave.py'
$settingsPath = Join-Path $dst 'settings.json'
$statePath = Join-Path $memoryRoot 'memory-install-state.json'
$manifestPath = Join-Path $memoryRoot 'installed-files-manifest.json'
$hookMarker = 'ai-company-base-session-autosave'

function Get-FileHashString($Path) {
    if (-not (Test-Path $Path)) { return $null }
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $hashBytes = $sha.ComputeHash($stream)
        return -join ($hashBytes | ForEach-Object { $_.ToString("x2") })
    } finally {
        $stream.Dispose()
    }
}

$agents = Get-ChildItem (Join-Path $src 'agents') -Filter *.md
$skills = Get-ChildItem (Join-Path $src 'skills') -Directory

function ConvertTo-Hashtable($Value) {
    if ($null -eq $Value) { return $null }
    if ($Value -is [System.Collections.IDictionary]) {
        $result = [ordered]@{}
        foreach ($key in $Value.Keys) { $result[$key] = ConvertTo-Hashtable $Value[$key] }
        return $result
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $result = [ordered]@{}
        foreach ($property in $Value.PSObject.Properties) { $result[$property.Name] = ConvertTo-Hashtable $property.Value }
        return $result
    }
    if ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string]) {
        $result = @()
        foreach ($item in $Value) { $result += ,(ConvertTo-Hashtable $item) }
        return ,$result
    }
    return $Value
}

function Read-Settings {
    if (-not (Test-Path $settingsPath)) { return [ordered]@{} }
    try {
        $raw = [System.IO.File]::ReadAllText($settingsPath, [System.Text.Encoding]::UTF8)
        $parsed = ConvertFrom-Json -InputObject $raw -ErrorAction Stop
        return ConvertTo-Hashtable $parsed
    } catch {
        throw "Không thể đọc $settingsPath dưới dạng JSON hợp lệ; không ghi đè file. Chi tiết: $($_.Exception.Message)"
    }
}

function Write-Settings($Settings) {
    $json = ConvertTo-Json -InputObject $Settings -Depth 100
    [System.IO.File]::WriteAllText($settingsPath, $json + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}

function Get-OwnedHook($Settings) {
    if (-not $Settings.Contains('hooks') -or $null -eq $Settings['hooks']) { return @() }
    if (-not $Settings['hooks'].Contains('SessionEnd')) { return @() }
    $owned = @()
    foreach ($entry in @($Settings['hooks']['SessionEnd'])) {
        $matched = $false
        foreach ($hook in @($entry['hooks'])) {
            if ($hook['type'] -eq 'command' -and $hook['command'] -like "*$hookMarker*") { $matched = $true }
        }
        if ($matched) { $owned += ,$entry }
    }
    return $owned
}

function Remove-OwnedHook($Settings) {
    if (-not $Settings.Contains('hooks') -or $null -eq $Settings['hooks']) { return }
    if (-not $Settings['hooks'].Contains('SessionEnd')) { return }
    $remaining = @()
    foreach ($entry in @($Settings['hooks']['SessionEnd'])) {
        $keptHooks = @()
        foreach ($hook in @($entry['hooks'])) {
            if (-not ($hook['type'] -eq 'command' -and $hook['command'] -like "*$hookMarker*")) { $keptHooks += ,$hook }
        }
        if ($keptHooks.Count -gt 0) {
            $entry['hooks'] = $keptHooks
            $remaining += ,$entry
        }
    }
    if ($remaining.Count -gt 0) { $Settings['hooks']['SessionEnd'] = $remaining }
    else { $Settings['hooks'].Remove('SessionEnd') }
    if ($Settings['hooks'].Count -eq 0) { $Settings.Remove('hooks') }
}

if ($Uninstall) {
    if (Test-Path $settingsPath) {
        $settings = Read-Settings
        Remove-OwnedHook $settings
        if (Test-Path $statePath) {
            try {
                $state = Get-Content $statePath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
                if ($state.ChangedAutoMemoryEnabled -and $settings.Contains('autoMemoryEnabled') -and $settings['autoMemoryEnabled'] -eq $true) {
                    if ($state.AutoMemoryEnabledWasPresent) { $settings['autoMemoryEnabled'] = [bool]$state.OriginalAutoMemoryEnabled }
                    else { $settings.Remove('autoMemoryEnabled') }
                }
            } catch {
                throw "Không đọc được metadata $statePath; dừng uninstall để tránh làm mất cấu hình. Chi tiết: $($_.Exception.Message)"
            }
        }
        Write-Settings $settings
    }
    $manifest = if (Test-Path $manifestPath) {
        try { Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop } catch { $null }
    } else { $null }

    foreach ($a in $agents) {
        $p = Join-Path $dst "agents\$($a.Name)"
        if (Test-Path $p) {
            $expected = if ($manifest -and $manifest.files -and $manifest.files.("agents/$($a.Name)")) { $manifest.files.("agents/$($a.Name)") } else { $null }
            $current = Get-FileHashString $p
            if ($null -eq $expected -or $expected -eq $current) {
                Remove-Item $p -Confirm:$false
                Write-Host "Đã gỡ agent  $($a.BaseName)"
            } else {
                Write-Host "Giữ lại agent đã bị người dùng sửa: $($a.BaseName)"
            }
        }
    }
    foreach ($s in $skills) {
        $skillDir = Join-Path $dst "skills\$($s.Name)"
        if (Test-Path $skillDir) {
            $canRemove = $true
            $installedFiles = Get-ChildItem $skillDir -Recurse -File
            foreach ($f in $installedFiles) {
                $rel = ($f.FullName.Substring($dst.Length)).TrimStart('\', '/').Replace('\', '/')
                $expected = if ($manifest -and $manifest.files -and $manifest.files.$rel) { $manifest.files.$rel } else { $null }
                $current = Get-FileHashString $f.FullName
                if ($null -ne $expected -and $expected -ne $current) {
                    $canRemove = $false
                    break
                }
            }
            if ($canRemove) {
                Remove-Item $skillDir -Recurse -Confirm:$false
                Write-Host "Đã gỡ lệnh  /$($s.Name)"
            } else {
                Write-Host "Giữ lại lệnh đã bị người dùng sửa: /$($s.Name)"
            }
        }
    }
    if (Test-Path $memoryRoot) { Remove-Item $memoryRoot -Recurse -Confirm:$false }
    return
}

# Parse settings before copying anything so malformed JSON leaves the profile untouched.
$settings = Read-Settings

New-Item -ItemType Directory -Force (Join-Path $dst 'agents'), (Join-Path $dst 'skills'), (Join-Path $memoryRoot 'scripts') | Out-Null

foreach ($a in $agents) {
    Copy-Item $a.FullName (Join-Path $dst 'agents') -Force
    Write-Host "Agent  $($a.BaseName)"
}
foreach ($s in $skills) {
    $target = Join-Path $dst "skills\$($s.Name)"
    if (Test-Path $target) { Remove-Item $target -Recurse -Confirm:$false }
    Copy-Item $s.FullName $target -Recurse
    Write-Host "Lệnh   /$($s.Name)"
}

Copy-Item (Join-Path $PSScriptRoot 'scripts\session_autosave.py') $autosaveScript -Force

# Lưu manifest SHA256 các file do toolkit cài để khi uninstall không gỡ nhầm file người dùng đã chỉnh sửa
$manifestEntries = [ordered]@{}
foreach ($a in $agents) {
    $p = Join-Path $dst "agents\$($a.Name)"
    $manifestEntries["agents/$($a.Name)"] = Get-FileHashString $p
}
foreach ($s in $skills) {
    $skillDir = Join-Path $dst "skills\$($s.Name)"
    foreach ($f in (Get-ChildItem $skillDir -Recurse -File)) {
        $rel = ($f.FullName.Substring($dst.Length)).TrimStart('\', '/').Replace('\', '/')
        $manifestEntries[$rel] = Get-FileHashString $f.FullName
    }
}
$manifestObj = [ordered]@{ files = $manifestEntries }
ConvertTo-Json $manifestObj -Depth 20 | Set-Content -Path $manifestPath -Encoding UTF8

$settings = Read-Settings
if (-not (Test-Path $statePath)) {
    $wasPresent = $settings.Contains('autoMemoryEnabled')
    $originalValue = if ($wasPresent) { [bool]$settings['autoMemoryEnabled'] } else { $false }
    $changed = (-not $wasPresent) -or ($settings['autoMemoryEnabled'] -ne $true)
    $state = [ordered]@{
        AutoMemoryEnabledWasPresent = $wasPresent
        OriginalAutoMemoryEnabled = $originalValue
        ChangedAutoMemoryEnabled = $changed
    }
    ConvertTo-Json $state -Depth 10 | Set-Content -Path $statePath -Encoding UTF8
}
$settings['autoMemoryEnabled'] = $true

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if ($python) {
    if (-not $settings.Contains('hooks') -or $null -eq $settings['hooks']) { $settings['hooks'] = [ordered]@{} }
    if (-not $settings['hooks'].Contains('SessionEnd') -or $null -eq $settings['hooks']['SessionEnd']) { $settings['hooks']['SessionEnd'] = @() }
    $hookCommand = '"' + $python.Source + '" "' + $autosaveScript + '" # ' + $hookMarker
    $existingOwned = Get-OwnedHook $settings
    if ($existingOwned.Count -eq 0) {
        $settings['hooks']['SessionEnd'] = @($settings['hooks']['SessionEnd']) + @([ordered]@{
            hooks = @([ordered]@{ type = 'command'; command = $hookCommand; timeout = 10 })
        })
    } else {
        foreach ($entry in $existingOwned) {
            foreach ($hook in @($entry['hooks'])) {
                if ($hook['type'] -eq 'command' -and $hook['command'] -like "*$hookMarker*") { $hook['command'] = $hookCommand }
            }
        }
    }
    Write-Host 'Đã bật auto-memory toàn cục và cài hook autosave theo project.'
} else {
    Write-Host 'Đã bật auto-memory toàn cục. Không tìm thấy Python; hook autosave phiên chưa được cài.'
    Write-Host 'Cài Python 3 rồi chạy lại install.ps1 để bật autosave.'
}
Write-Settings $settings

Write-Host ""
Write-Host "Xong: $($agents.Count) agent, $($skills.Count) lệnh đã cài vào $dst"
Write-Host "Mở phiên Claude Code mới để dùng /bat-dau, /phan-tich, /chuyen-doi, /tien-do, /graphify ở bất kỳ thư mục nào."
