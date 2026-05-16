# Build the QwenPaw core/lib wheel for product-layer packaging.
# Run from repo root:
#   powershell -ExecutionPolicy Bypass -File scripts\build_core_wheel.ps1

param(
  [string]$OutDir = "dist-core"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

$ResolvedOutDir = Join-Path $RepoRoot $OutDir
Write-Host "[build_core_wheel] Building qwenpaw core wheel -> $ResolvedOutDir"

python -m pip install --quiet build

if (Test-Path $ResolvedOutDir) {
  Remove-Item -Path (Join-Path $ResolvedOutDir "*") -Force -ErrorAction SilentlyContinue
} else {
  New-Item -ItemType Directory -Force -Path $ResolvedOutDir | Out-Null
}

python -m build --wheel --outdir $ResolvedOutDir .
if ($LASTEXITCODE -ne 0) {
  throw "python -m build failed with exit code $LASTEXITCODE"
}

Write-Host "[build_core_wheel] Done. Wheel(s) in: $ResolvedOutDir"
