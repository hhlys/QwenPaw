# Build an offline Linux x86_64 runtime bundle for customer sites that cannot
# access the internet and cannot run Docker.
#
# Run from repo root:
#   powershell -ExecutionPolicy Bypass -File scripts\build_offline_linux_bundle.ps1

param(
  [string]$Version = "1.1.7",
  [string]$PythonStandaloneUrl = "https://github.com/astral-sh/python-build-standalone/releases/download/20260510/cpython-3.11.15%2B20260510-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz",
  [string]$WheelPath = "",
  [string]$OutDir = "dist-offline",
  [switch]$SkipWheelBuild,
  [switch]$SkipDependencyDownload
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

$OutAbs = Join-Path $RepoRoot $OutDir
$TmpRoot = Join-Path $RepoRoot ".tmp\offline-linux"
$StageRoot = Join-Path $TmpRoot "stage"
$BundleName = "qwenpaw-offline-linux-x86_64-$Version"
$BundleRoot = Join-Path $StageRoot $BundleName
$Wheelhouse = Join-Path $TmpRoot "wheelhouse"
$RuntimeArchive = Join-Path $TmpRoot "python-standalone.tar.gz"
$RuntimeExtract = Join-Path $TmpRoot "python-runtime"

function Reset-Dir([string]$Path) {
  if (Test-Path $Path) {
    Remove-Item -Recurse -Force $Path
  }
  New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Download-FileWithRetry([string]$Url, [string]$OutFile, [int]$Attempts = 5) {
  $tmpFile = "$OutFile.part"
  if (Test-Path $tmpFile) {
    Remove-Item -Force $tmpFile
  }

  for ($i = 1; $i -le $Attempts; $i++) {
    Write-Host "[offline_bundle] Download attempt $i/${Attempts}: $Url"
    try {
      Invoke-WebRequest -Uri $Url -OutFile $tmpFile -Headers @{ "User-Agent" = "QwenPawOfflineBuilder" } -UseBasicParsing
      Move-Item -Force $tmpFile $OutFile
      return
    } catch {
      Write-Warning "[offline_bundle] Invoke-WebRequest failed: $($_.Exception.Message)"
      if (Test-Path $tmpFile) {
        Remove-Item -Force $tmpFile -ErrorAction SilentlyContinue
      }
      $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
      if ($curl) {
        & curl.exe -L --fail --retry 5 --retry-delay 3 --connect-timeout 30 --output $tmpFile $Url
        if ($LASTEXITCODE -eq 0 -and (Test-Path $tmpFile)) {
          Move-Item -Force $tmpFile $OutFile
          return
        }
        Remove-Item -Force $tmpFile -ErrorAction SilentlyContinue
      }
      if ($i -lt $Attempts) {
        Start-Sleep -Seconds (3 * $i)
      }
    }
  }

  throw "Failed to download $Url after $Attempts attempts."
}

New-Item -ItemType Directory -Force -Path $OutAbs, $TmpRoot | Out-Null

if (-not $SkipWheelBuild -and [string]::IsNullOrWhiteSpace($WheelPath)) {
  Write-Host "[offline_bundle] Building QwenPaw wheel..."
  powershell -ExecutionPolicy Bypass -File scripts\build_core_wheel.ps1 -OutDir dist-core
}

if ([string]::IsNullOrWhiteSpace($WheelPath)) {
  $Wheel = Get-ChildItem -Path (Join-Path $RepoRoot "dist-core") -Filter "qwenpaw-*.whl" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
  if (-not $Wheel) {
    throw "No qwenpaw wheel found in dist-core. Build one first or pass -WheelPath."
  }
  $WheelPath = $Wheel.FullName
}

Write-Host "[offline_bundle] Using wheel: $WheelPath"

Reset-Dir $StageRoot
Reset-Dir $Wheelhouse
New-Item -ItemType Directory -Force -Path `
  (Join-Path $BundleRoot "app"), `
  (Join-Path $BundleRoot "runtime"), `
  (Join-Path $BundleRoot "wheels"), `
  (Join-Path $BundleRoot "data"), `
  (Join-Path $BundleRoot "logs"), `
  (Join-Path $BundleRoot "run") | Out-Null

Copy-Item $WheelPath -Destination (Join-Path $BundleRoot "app") -Force
Copy-Item "deploy\offline-linux\*" -Destination $BundleRoot -Recurse -Force
Copy-Item "docs\offline-linux-runtime-deploy.zh.md" -Destination (Join-Path $BundleRoot "README_INSTALL.zh.md") -Force
Copy-Item (Join-Path $BundleRoot "env.example") -Destination (Join-Path $BundleRoot "env.sh") -Force

if (-not (Test-Path $RuntimeArchive)) {
  Write-Host "[offline_bundle] Downloading Python standalone runtime..."
  Download-FileWithRetry -Url $PythonStandaloneUrl -OutFile $RuntimeArchive
} else {
  Write-Host "[offline_bundle] Reusing cached Python runtime: $RuntimeArchive"
}

Reset-Dir $RuntimeExtract
Write-Host "[offline_bundle] Extracting Python runtime..."
tar -xzf $RuntimeArchive -C $RuntimeExtract
if ($LASTEXITCODE -ne 0) {
  throw "Failed to extract Python runtime archive."
}

$PythonDir = Get-ChildItem -Path $RuntimeExtract -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName "bin\python3") -or Test-Path (Join-Path $_.FullName "install\bin\python3") } |
  Select-Object -First 1
if (-not $PythonDir) {
  throw "Could not locate extracted Python runtime directory."
}
Copy-Item $PythonDir.FullName -Destination (Join-Path $BundleRoot "runtime\python") -Recurse -Force

if (-not $SkipDependencyDownload) {
  Write-Host "[offline_bundle] Downloading Linux x86_64 wheels..."
  python -m pip download `
    --dest $Wheelhouse `
    --only-binary=:all: `
    --platform manylinux2014_x86_64 `
    --platform manylinux_2_28_x86_64 `
    --implementation cp `
    --python-version 311 `
    --abi cp311 `
    --abi abi3 `
    --abi none `
    $WheelPath
  if ($LASTEXITCODE -ne 0) {
    throw "pip download failed. Check whether all dependencies provide Linux wheels."
  }
} else {
  Write-Host "[offline_bundle] Skipping dependency download by request."
}

Copy-Item (Join-Path $Wheelhouse "*") -Destination (Join-Path $BundleRoot "wheels") -Force

Write-Host "[offline_bundle] Writing version marker..."
@"
name=qwenpaw
version=$Version
python_runtime=$PythonStandaloneUrl
created_at=$(Get-Date -Format o)
"@ | Set-Content -Encoding UTF8 (Join-Path $BundleRoot "VERSION")

$TarPath = Join-Path $OutAbs "$BundleName.tar.gz"
if (Test-Path $TarPath) {
  Remove-Item -Force $TarPath
}

Write-Host "[offline_bundle] Creating archive: $TarPath"
Push-Location $StageRoot
try {
  tar -czf $TarPath $BundleName
  if ($LASTEXITCODE -ne 0) {
    throw "tar failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

Write-Host "[offline_bundle] Done: $TarPath"
