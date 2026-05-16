# Install hClaw product layer with a QwenPaw core wheel.
# Run from this branch root:
#   powershell -ExecutionPolicy Bypass -File scripts\build_product.ps1 -CoreWheel ..\..\dist-core\qwenpaw-1.1.7-py3-none-any.whl

param(
  [Parameter(Mandatory = $true)]
  [string]$CoreWheel,
  [switch]$Editable,
  [switch]$NoDeps
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

$ResolvedCoreWheel = Resolve-Path $CoreWheel
Write-Host "[build_product] Installing QwenPaw core wheel: $ResolvedCoreWheel"
if ($NoDeps) {
  python -m pip install --no-deps --force-reinstall $ResolvedCoreWheel
} else {
  python -m pip install --force-reinstall $ResolvedCoreWheel
}

if ($Editable) {
  Write-Host "[build_product] Installing hClaw product layer in editable mode"
  if ($NoDeps) {
    python -m pip install --no-deps -e .
  } else {
    python -m pip install -e .
  }
} else {
  Write-Host "[build_product] Installing hClaw product layer"
  if ($NoDeps) {
    python -m pip install --no-deps .
  } else {
    python -m pip install .
  }
}

Write-Host "[build_product] Done. Try: hclaw --help"
