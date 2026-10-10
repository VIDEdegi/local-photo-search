# Run inside the disposable guest AFTER its interactive installer completes.
# Uses only Windows PowerShell/.NET; does not download models or change photos.
param([Parameter(Mandatory=$true)][string]$InstallDirectory,
      [string]$Results='C:\LPS-Results', [string]$Model)
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Path $Results -Force | Out-Null
$report=[ordered]@{ os=[Environment]::OSVersion.Version.ToString(); x64=[Environment]::Is64BitProcess; developmentTools=@{} }
foreach($tool in @('python','python3','node','npm','rustc','cargo','cl')) {
  $command=Get-Command $tool -ErrorAction SilentlyContinue
  $report.developmentTools[$tool]=if($command){$command.Source}else{$null}
}
$worker=Join-Path $InstallDirectory 'worker/media-search-worker.exe'
if(-not(Test-Path -LiteralPath $worker)){throw 'Installed Worker not found.'}
$data=Join-Path $env:LOCALAPPDATA 'LocalPhotoSearchCleanTest'
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$worker
$start.Arguments='--data "'+$data+'"'
$start.UseShellExecute=$false
$start.CreateNoWindow=$true
$start.RedirectStandardInput=$true
$start.RedirectStandardOutput=$true
$start.RedirectStandardError=$true
$start.StandardOutputEncoding=New-Object System.Text.UTF8Encoding($false)
$start.StandardErrorEncoding=New-Object System.Text.UTF8Encoding($false)
$start.EnvironmentVariables['PATH']=$env:WINDIR+'\System32'
$start.EnvironmentVariables.Remove('PYTHONPATH')
$start.EnvironmentVariables.Remove('PYTHONHOME')
$process=New-Object System.Diagnostics.Process
$process.StartInfo=$start
$process.Start() | Out-Null
$inputWriter=[IO.StreamWriter]::new($process.StandardInput.BaseStream,[Text.UTF8Encoding]::new($false))
$inputWriter.AutoFlush=$true
$errors=$process.StandardError.ReadToEndAsync()
function Send-Request($id,$method,$parameters) {
  $request=@{version=1;id=$id;method=$method;params=$parameters} | ConvertTo-Json -Compress -Depth 8
  $inputWriter.WriteLine($request)
  $line=$process.StandardOutput.ReadLineAsync()
  if(-not $line.Wait(120000)){throw 'Worker response timed out.'}
  if(-not $line.Result){throw 'Worker terminated without a response.'}
  return ($line.Result | ConvertFrom-Json)
}
try {
  $report.environment=Send-Request 1 'environment' @{}
  if($report.environment.error -or -not $report.environment.result.python_bundled){throw 'Bundled Worker environment check failed.'}
  $report.initialStatus=Send-Request 2 'status' @{}
  if($report.initialStatus.error -or $report.initialStatus.result.total -ne 0){throw 'A fresh isolated index is required.'}
  $report.noModelSearch=Send-Request 3 'search' @{text='photo'}
  if(-not $report.noModelSearch.error){throw 'Missing-model search did not produce the expected error.'}
  if($Model) {
    if(-not(Test-Path -LiteralPath $Model)){throw 'Supplied read-only model not found.'}
    $report.modelSetup=Send-Request 4 'configure' @{model_path=$Model;backend='cpu'}
    if($report.modelSetup.error){throw 'Read-only model configuration failed.'}
    $report.cpuDiagnostic=Send-Request 5 'diagnose' @{}
    if($report.cpuDiagnostic.error -or -not $report.cpuDiagnostic.result.ok){throw 'CPU diagnostic failed; see the saved record.'}
  }
  $report.shutdown=Send-Request 6 'shutdown' @{}
  if(-not $report.shutdown.result.ok){throw 'Shutdown acknowledgement failed.'}
  if(-not $process.WaitForExit(20000)){throw 'Graceful shutdown timed out.'}
  $report.workerExit=$process.ExitCode
  if($report.workerExit -ne 0){throw 'Worker exited abnormally.'}
} finally {
  if(-not $process.HasExited){$process.Kill();$process.WaitForExit()}
  $errors.Wait(10000) | Out-Null
  if($errors.IsCompleted){[IO.File]::WriteAllText((Join-Path $Results 'worker.log'),$errors.Result)}
  $report | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 (Join-Path $Results 'smoke.json')
  $inputWriter.Dispose()
  $process.Dispose()
}
Write-Output 'Guest smoke record saved. Complete the manual acceptance matrix too.'
