param(
    [string]$WorkingDir = "",
    [string]$SourceDir = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($WorkingDir)) {
    if ($env:QWENPAW_WORKING_DIR) {
        $WorkingDir = $env:QWENPAW_WORKING_DIR
    } else {
        $WorkingDir = Join-Path $HOME ".qwenpaw"
    }
}

if ([string]::IsNullOrWhiteSpace($SourceDir)) {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
    $SourceDir = Join-Path $RepoRoot "examples\custom_channels\clawhub_chat"
}

$TargetDir = Join-Path $WorkingDir "custom_channels\clawhub_chat"

if (!(Test-Path $SourceDir)) {
    throw "Source directory not found: $SourceDir"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $TargetDir) | Out-Null
if (Test-Path $TargetDir) {
    Remove-Item -LiteralPath $TargetDir -Recurse -Force
}
Copy-Item -LiteralPath $SourceDir -Destination $TargetDir -Recurse

Write-Host "Installed clawhub_chat custom channel to: $TargetDir"
Write-Host "Next: restart qwenpaw app. Optional: enable channels.clawhub_chat in agent.json for health visibility."
