param(
    [string]$ImageTag = "qwenpaw:local",
    [string]$TarPath = "",
    [switch]$BuildRuntime,
    [switch]$BuildConsole
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $RepoRoot

if ([string]::IsNullOrWhiteSpace($env:NODE_OPTIONS)) {
    $env:NODE_OPTIONS = "--max-old-space-size=6144"
}

Write-Host "[build_local_image] Building wheel..."
$WheelBuildArgs = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $RepoRoot "scripts\wheel_build.ps1"))
if (-not $BuildConsole) {
    $WheelBuildArgs += "-SkipConsole"
}
PowerShell @WheelBuildArgs
if ($LASTEXITCODE -ne 0) { throw "wheel_build.ps1 failed with exit code $LASTEXITCODE" }

Write-Host "[build_local_image] Exporting runtime requirements..."
python scripts\export_runtime_requirements.py --out build/runtime-requirements.txt
if ($LASTEXITCODE -ne 0) { throw "export_runtime_requirements.py failed with exit code $LASTEXITCODE" }

if ($BuildRuntime -or -not (docker image inspect qwenpaw-runtime:local *> $null)) {
    Write-Host "[build_local_image] Building runtime base image: qwenpaw-runtime:local"
    docker build -f deploy/Dockerfile.runtime -t qwenpaw-runtime:local .
    if ($LASTEXITCODE -ne 0) { throw "runtime docker build failed with exit code $LASTEXITCODE" }
}

Write-Host "[build_local_image] Building Docker image: $ImageTag"
docker build -f deploy/Dockerfile.wheel -t $ImageTag .
if ($LASTEXITCODE -ne 0) { throw "docker build failed with exit code $LASTEXITCODE" }

if (![string]::IsNullOrWhiteSpace($TarPath)) {
    Write-Host "[build_local_image] Exporting image to: $TarPath"
    docker save -o $TarPath $ImageTag
    if ($LASTEXITCODE -ne 0) { throw "docker save failed with exit code $LASTEXITCODE" }
}

Write-Host "[build_local_image] Done: $ImageTag"
