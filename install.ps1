# Cài (hoặc gỡ) bộ công ty AI vào thư mục Claude dùng chung: %USERPROFILE%\.claude
#   Cài / cập nhật:  powershell -ExecutionPolicy Bypass -File install.ps1
#   Gỡ:              powershell -ExecutionPolicy Bypass -File install.ps1 -Uninstall
param([switch]$Uninstall)

$ErrorActionPreference = 'Stop'
$src = Join-Path $PSScriptRoot '.claude'
$dst = Join-Path $HOME '.claude'

$agents = Get-ChildItem (Join-Path $src 'agents') -Filter *.md
$skills = Get-ChildItem (Join-Path $src 'skills') -Directory

if ($Uninstall) {
    foreach ($a in $agents) {
        $p = Join-Path $dst "agents\$($a.Name)"
        if (Test-Path $p) { Remove-Item $p -Confirm:$false; Write-Host "Đã gỡ agent  $($a.BaseName)" }
    }
    foreach ($s in $skills) {
        $p = Join-Path $dst "skills\$($s.Name)"
        if (Test-Path $p) { Remove-Item $p -Recurse -Confirm:$false; Write-Host "Đã gỡ lệnh  /$($s.Name)" }
    }
    return
}

New-Item -ItemType Directory -Force (Join-Path $dst 'agents'), (Join-Path $dst 'skills') | Out-Null

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

Write-Host ""
Write-Host "Xong: $($agents.Count) agent, $($skills.Count) lệnh đã cài vào $dst"
Write-Host "Mở phiên Claude Code mới để dùng /bat-dau, /chuyen-doi, /tien-do ở bất kỳ thư mục nào."
