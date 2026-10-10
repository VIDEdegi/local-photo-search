# Private signing material stays in ignored data/private-signing. No publication.
. "$PSScriptRoot/env.ps1"
$keyDir = Join-Path $projectRoot 'data/private-signing'
$env:TAURI_SIGNING_PRIVATE_KEY = Join-Path $keyDir 'updater.key'
$secret = Get-Content (Join-Path $keyDir 'password.dpapi') | ConvertTo-SecureString
$credential = [System.Management.Automation.PSCredential]::new('signer', $secret)
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = $credential.GetNetworkCredential().Password
try {
  $bootstrapper=Join-Path $env:CARGO_TARGET_DIR '.tauri/MicrosoftEdgeWebview2Setup.exe'
  if(Test-Path -LiteralPath $bootstrapper){
    $signature=Get-AuthenticodeSignature -LiteralPath $bootstrapper
    if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation(,|$)'){throw 'Invalid Microsoft WebView2 bootstrapper'}
  }
  npm.cmd run tauri -- build @args
  if ($LASTEXITCODE -ne 0) { throw 'Signed build failed' }
  $signature=Get-AuthenticodeSignature -LiteralPath $bootstrapper
  if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation(,|$)'){throw 'Invalid bundled Microsoft WebView2 bootstrapper'}
} finally {
  Remove-Item Env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD -ErrorAction SilentlyContinue
  Remove-Item Env:TAURI_SIGNING_PRIVATE_KEY -ErrorAction SilentlyContinue
}
