# Project-only CPython security update; never changes system Python or old venv.
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot -Parent
$package=Join-Path $taskRoot 'data/release-tests/rc-audit/python.3.14.8.nupkg'
New-Item -ItemType Directory -Path (Split-Path $package -Parent) -Force | Out-Null
$expected='CE85F674D9A63029F709CBFF7A3DA1C6BC5BFCFAEFDD9999F98FA0290470C454'
if(-not(Test-Path -LiteralPath $package)) {
  Invoke-WebRequest -Uri 'https://api.nuget.org/v3-flatcontainer/python/3.14.8/python.3.14.8.nupkg' -OutFile $package
}
if((Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash -ne $expected){throw 'CPython package differs from the audited official artifact.'}
$runtime=Join-Path $taskRoot 'tools/python-runtime-3.14.8'
if(-not(Test-Path -LiteralPath (Join-Path $runtime 'tools/python.exe'))) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [IO.Compression.ZipFile]::ExtractToDirectory($package,$runtime)
}
$basePython=Join-Path $runtime 'tools/python.exe'
foreach($binary in @('python.exe','python314.dll')) {
  $signature=Get-AuthenticodeSignature -LiteralPath (Join-Path $runtime "tools/$binary")
  if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Python Software Foundation(,|$)'){throw 'CPython publisher signature verification failed.'}
}
$destination=Join-Path $taskRoot 'tools/python-build-3.14.8'
if(-not(Test-Path -LiteralPath (Join-Path $destination 'Scripts/python.exe'))) {
  & $basePython -m venv --without-pip $destination
  if($LASTEXITCODE -ne 0){throw 'Project build environment creation failed.'}
  # Existing pinned third-party wheels share the CPython 3.14 ABI. Reuse them
  # without fetching models/dependencies or copying old Python runtime DLLs.
  $oldPackages=Join-Path $taskRoot 'tools/python/Lib/site-packages'
  $newPackages=Join-Path $destination 'Lib/site-packages'
  Copy-Item -LiteralPath (Get-ChildItem -LiteralPath $oldPackages -Force).FullName -Destination $newPackages -Recurse -Force
}
$python=Join-Path $destination 'Scripts/python.exe'
& $python -c "import sys,ssl,importlib.metadata; assert sys.version_info[:3]==(3,14,8); assert ssl.OPENSSL_VERSION.startswith('OpenSSL 3.5.9 '); assert importlib.metadata.version('litert-lm-api')=='0.18.0'; assert importlib.metadata.version('Pillow')=='12.3.0'; assert importlib.metadata.version('PyInstaller')=='6.22.3'; print(sys.version); print(ssl.OPENSSL_VERSION)"
if($LASTEXITCODE -ne 0){throw 'Pinned runtime/dependency validation failed.'}
Copy-Item -LiteralPath (Join-Path $runtime 'tools/LICENSE.txt') -Destination (Join-Path $taskRoot 'licenses/python/CPython/LICENSE.txt')
Write-Output 'Project runtime ready; system Python and previous project environment retained.'
