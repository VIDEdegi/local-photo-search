$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
  & cl.exe /nologo /O2 /fp:strict /GS- /LD worker/native/exact_dot.c /Fo:tmp/exact_dot.obj /Fe:worker/native/exact-search.dll /link /NODEFAULTLIB /NOENTRY /MACHINE:X64 /IMPLIB:tmp/exact-search.lib
  if ($LASTEXITCODE -ne 0) { throw 'Exact search helper build failed' }
} finally { Pop-Location }
