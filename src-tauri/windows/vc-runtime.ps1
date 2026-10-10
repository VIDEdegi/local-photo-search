# Installer prerequisite only. Does not read photo or application data.
param([ValidateSet('Check','Download')][string]$Mode, [string]$Destination)
$ErrorActionPreference = 'Stop'
# A setup launched from PowerShell 7 can inherit an incompatible module path.
# Use only Windows' own 5.1 modules in this short-lived prerequisite process.
$env:PSModulePath = Join-Path $PSHOME 'Modules'
try {
  if ($Mode -eq 'Check') {
    if (-not [Environment]::Is64BitProcess) { exit 11 }
    foreach ($name in @('msvcp140.dll','vcruntime140.dll','vcruntime140_1.dll')) {
      $dll = Join-Path $env:WINDIR "System32/$name"
      if (-not (Test-Path -LiteralPath $dll)) { exit 10 }
      $versionText = (Get-Item -LiteralPath $dll).VersionInfo.FileVersion
      if ($versionText -notmatch '^\d+\.\d+\.\d+\.\d+') { exit 10 }
      if ([version]($Matches[0]) -lt [version]'14.44.0.0') { exit 10 }
    }
    exit 0
  }
  if (-not $Destination -or [IO.Path]::GetFileName($Destination) -ne 'VC_redist.x64.exe') { exit 12 }
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -UseBasicParsing -Uri 'https://aka.ms/vs/17/release/VC_redist.x64.exe' -OutFile $Destination -TimeoutSec 120
  $signature = Get-AuthenticodeSignature -LiteralPath $Destination
  if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(^|,\s*)O=Microsoft Corporation(,|$)') { exit 13 }
  $versionInfo = (Get-Item -LiteralPath $Destination).VersionInfo
  if ($versionInfo.ProductName -notmatch '^Microsoft Visual C\+\+ .*Redistributable \(x64\)') { exit 14 }
  if ($versionInfo.FileVersion -notmatch '^\d+\.\d+\.\d+\.\d+' -or [version]($Matches[0]) -lt [version]'14.44.0.0') { exit 14 }
  exit 0
} catch {
  # Technical errors may contain a temporary path; no private data is read.
  # Keep ASCII so Windows PowerShell 5.1 can read this UTF-8 source without BOM.
  # The NSIS dialog supplies the Japanese user-facing recovery instructions.
  Write-Error 'Microsoft runtime check/download failed. Install the official offline package and retry.' -ErrorAction Continue
  Write-Error $_.Exception.Message -ErrorAction Continue
  exit 15
}
