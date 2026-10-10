$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
  $bootstrapper = Join-Path $env:CARGO_TARGET_DIR '.tauri/MicrosoftEdgeWebview2Setup.exe'
  function Assert-MicrosoftBootstrapper {
    if (Test-Path -LiteralPath $bootstrapper) {
      $signature = Get-AuthenticodeSignature -LiteralPath $bootstrapper
      if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(^|,\s*)O=Microsoft Corporation(,|$)') {
        throw 'WebView2 Bootstrapper has no valid Microsoft signature; distribution build rejected.'
      }
    }
  }
  Assert-MicrosoftBootstrapper
  & "$PSScriptRoot/build-worker.ps1"
  & npm.cmd run tauri -- build
  if ($LASTEXITCODE -ne 0) { throw 'Windows build failed' }
  if (-not (Test-Path -LiteralPath $bootstrapper)) { throw 'Bundled WebView2 Bootstrapper was not found.' }
  Assert-MicrosoftBootstrapper
} finally { Pop-Location }
