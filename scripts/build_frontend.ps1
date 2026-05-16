# Build the hClaw frontend source under web/console and publish it to web/dist.
# Run from this branch root:
#   powershell -ExecutionPolicy Bypass -File scripts\build_frontend.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

$ConsoleDir = Join-Path $RepoRoot "web\console"
$DistFrom = Join-Path $ConsoleDir "dist"
$DistTo = Join-Path $RepoRoot "web\dist"

Write-Host "[build_frontend] Building frontend in: $ConsoleDir"
Push-Location $ConsoleDir
try {
  npm ci
  if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE" }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "npm run build failed with exit code $LASTEXITCODE" }
} finally {
  Pop-Location
}

Write-Host "[build_frontend] Copying $DistFrom -> $DistTo"
if (Test-Path $DistTo) {
  Remove-Item -Path (Join-Path $DistTo "*") -Recurse -Force -ErrorAction SilentlyContinue
} else {
  New-Item -ItemType Directory -Force -Path $DistTo | Out-Null
}
Copy-Item -Path (Join-Path $DistFrom "*") -Destination $DistTo -Recurse -Force

Write-Host "[build_frontend] Done."
