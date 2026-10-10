$projectRoot = Split-Path $PSScriptRoot -Parent
$env:TEMP = Join-Path $projectRoot 'tmp'
$env:TMP = $env:TEMP
$env:RUSTUP_HOME = Join-Path $projectRoot 'tools/rustup'
$env:CARGO_HOME = Join-Path $projectRoot 'tools/cargo'
$env:CARGO_TARGET_DIR = Join-Path $projectRoot 'target'
$env:npm_config_cache = Join-Path $projectRoot 'tools/npm-cache'
$env:PIP_CACHE_DIR = Join-Path $projectRoot 'tools/pip-cache'
$env:PYINSTALLER_CONFIG_DIR = Join-Path $projectRoot 'tools/pyinstaller-cache'
$env:TAURI_BUNDLER_TOOLS = Join-Path $projectRoot 'tools/tauri-bundler'
$env:MEDIA_SEARCH_DATA = Join-Path $projectRoot 'data'
$env:MEDIA_SEARCH_BUILD_PYTHON = Join-Path $projectRoot 'tools/python-build-3.14.8/Scripts/python.exe'
$env:PATH = "$(Join-Path $env:CARGO_HOME 'bin');$(Join-Path $projectRoot 'tools/python-build-3.14.8/Scripts');$(Join-Path $projectRoot 'tools/python/Scripts');$env:PATH"
$msvc = Get-ChildItem (Join-Path $projectRoot 'tools/msvc/VC/Tools/MSVC') -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
$sdk = Get-ChildItem (Join-Path $projectRoot 'tools/msvc/Windows Kits/10/Lib') -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
if ($msvc -and $sdk) {
  $sdkRoot = Join-Path $projectRoot 'tools/msvc/Windows Kits/10'
  $env:VSCMD_ARG_HOST_ARCH = 'x64'
  $env:VSCMD_ARG_TGT_ARCH = 'x64'
  $env:VCToolsInstallDir = "$($msvc.FullName)/"
  $env:WindowsSdkDir = "$sdkRoot/"
  $env:WindowsSDKVersion = "$($sdk.Name)/"
  $env:PATH = "$($msvc.FullName)/bin/Hostx64/x64;$sdkRoot/bin/$($sdk.Name)/x64;$env:PATH"
  $env:INCLUDE = "$($msvc.FullName)/include;$sdkRoot/Include/$($sdk.Name)/ucrt;$sdkRoot/Include/$($sdk.Name)/shared;$sdkRoot/Include/$($sdk.Name)/um"
  $env:LIB = "$($msvc.FullName)/lib/x64;$sdkRoot/Lib/$($sdk.Name)/ucrt/x64;$sdkRoot/Lib/$($sdk.Name)/um/x64"
}

