# Prepare configurations only. Never enables Sandbox or launches installers.
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$testRoot=Join-Path $taskRoot 'data/release-tests/clean-windows'
$inputRoot=Join-Path $testRoot 'input'
$resultRoot=Join-Path $testRoot 'results'
New-Item -ItemType Directory -Path $inputRoot,$resultRoot -Force | Out-Null
$version=(Get-Content (Join-Path $taskRoot 'src-tauri/tauri.conf.json') -Raw | ConvertFrom-Json).version
$installer=Join-Path $taskRoot "target/release/bundle/nsis/Local Photo Search_${version}_x64-setup.exe"
Copy-Item -LiteralPath $installer -Destination $inputRoot
$oldInstaller=Join-Path $taskRoot 'target/release/bundle/nsis/Local Photo Search_0.1.1_x64-setup.exe'
if(Test-Path -LiteralPath $oldInstaller){Copy-Item -LiteralPath $oldInstaller -Destination $inputRoot}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'clean-windows-smoke.ps1') -Destination $inputRoot
Copy-Item -LiteralPath (Join-Path $taskRoot 'docs/CLEAN_WINDOWS_ACCEPTANCE.md') -Destination $inputRoot
foreach($mode in @('offline','online')) {
  $network=if($mode -eq 'offline'){'Disable'}else{'Default'}
  $xml=@"
<Configuration>
  <Networking>$network</Networking>
  <MappedFolders>
    <MappedFolder><HostFolder>$([Security.SecurityElement]::Escape($inputRoot))</HostFolder><SandboxFolder>C:\LPS-Input</SandboxFolder><ReadOnly>true</ReadOnly></MappedFolder>
    <MappedFolder><HostFolder>$([Security.SecurityElement]::Escape($resultRoot))</HostFolder><SandboxFolder>C:\LPS-Results</SandboxFolder><ReadOnly>false</ReadOnly></MappedFolder>
  </MappedFolders>
</Configuration>
"@
  [IO.File]::WriteAllText((Join-Path $testRoot "$mode.wsb"),$xml)
}
Get-FileHash -LiteralPath $installer -Algorithm SHA256 | Format-List
Write-Output "Prepared only: $testRoot"
