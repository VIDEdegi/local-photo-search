$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
Push-Location (Split-Path $PSScriptRoot -Parent)
try { npm.cmd run desktop:dev } finally { Pop-Location }
