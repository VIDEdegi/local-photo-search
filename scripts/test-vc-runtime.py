"""Actual Windows PowerShell 5.1, signed fixtures; no system runtime installation.

Only Invoke-WebRequest is replaced for bounded failure/signature tests. The
earlier separately recorded real official download is the positive fixture.
"""
import json,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
shell=Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
script=root/'src-tauri/windows/vc-runtime.ps1'
official=root/'tmp/VC_redist.x64.exe'
assert official.is_file(), 'Obtain the official signed VC package for the audit first'
def literal(path):return "'"+str(path).replace("'","''")+"'"
report={'shell':'Windows PowerShell 5.1 x64','network_failures_are_injected':True,'installed_runtime_check':None,'cases':{}}
check=subprocess.run([str(shell),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(script),'-Mode','Check'],capture_output=True,timeout=30)
assert check.returncode==0,check.stderr
report['installed_runtime_check']=0
with tempfile.TemporaryDirectory(prefix='vc-check-',dir=root/'tmp') as directory:
    folder=Path(directory)
    for name,fixture,expected in (
        ('official_signature_version',official,0),
        ('unsigned_rejected',root/'target/release/embeddinggemma-media-search.exe',13),
        ('signed_wrong_product_rejected',root/'target/.tauri/MicrosoftEdgeWebview2Setup.exe',14),
        ('offline_recoverable',None,15),
        ('invalid_destination_rejected',official,12)):
        destination=folder/('wrong.exe' if name=='invalid_destination_rejected' else 'VC_redist.x64.exe')
        body=f'Copy-Item -LiteralPath {literal(fixture)} -Destination $OutFile' if fixture else "throw 'Injected offline test'"
        harness=folder/'fixture.ps1'
        harness.write_text("function Invoke-WebRequest { param([switch]$UseBasicParsing,$Uri,$OutFile,$TimeoutSec) "+body+" }\n& "+literal(script)+" -Mode Download -Destination "+literal(destination)+"\nexit $LASTEXITCODE\n",encoding='ascii')
        result=subprocess.run([str(shell),'-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(harness)],capture_output=True,timeout=45)
        assert result.returncode==expected,(name,result.returncode,result.stderr)
        report['cases'][name]=result.returncode
out=root/'data/release-tests/rc-audit/vc-runtime.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
