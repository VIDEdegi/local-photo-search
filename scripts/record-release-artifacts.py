"""Final development artifacts including generated QA uninstaller; no signing."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
import pefile
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'src-tauri/tauri.conf.json').read_text())['version']
assert version in ('1.0.0-dev.2','1.0.0'),'Unexpected release version'
paths=[('installer',root/f'target/release/bundle/nsis/SakuLoca_{version}_x64-setup.exe'),
       ('application',root/'target/release/SakuLoca.exe'),
       ('worker',root/'dist-worker/media-search-worker/media-search-worker.exe'),
       ('qa_uninstaller_path_dependent',root/'data/release-tests/installed-qa/uninstall.exe'),
       ('official_webview2_bootstrapper',root/'target/.tauri/MicrosoftEdgeWebview2Setup.exe')]
records=[]
for kind,path in paths:
    assert path.is_file(),path
    pe=pefile.PE(str(path));version_info={}
    for blocks in getattr(pe,'FileInfo',[]):
        for block in blocks:
            for table in getattr(block,'StringTable',[]):
                version_info.update({k.decode():v.decode(errors='replace') for k,v in table.entries.items()})
    pe.close()
    escaped=str(path).replace("'","''")
    shell=Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
    env=dict(os.environ,PSModulePath=str(shell.parent/'Modules'))
    signature=subprocess.check_output([str(shell),'-NoProfile','-Command',f"$ErrorActionPreference='Stop';$s=Get-AuthenticodeSignature -LiteralPath '{escaped}';@{{status=$s.Status.ToString();publisher=$s.SignerCertificate.Subject}}|ConvertTo-Json -Compress"],text=True,env=env)
    records.append({'kind':kind,'path':path.relative_to(root).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pe_version':version_info,'authenticode':json.loads(signature)})
report={'version':version,'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=root).strip(),'public_release':False,'application_license_selected':True,'application_distribution':'free and open-source (Apache-2.0)','files':records}
out=root/'data/release-tests/rc-audit'
(out/'artifacts.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'SHA256SUMS.txt').write_text('\n'.join(f"{r['sha256']}  {r['path']}" for r in records)+'\n',encoding='utf-8')
print(json.dumps({'version':version,'files':len(records),'installer_bytes':records[0]['bytes'],'installer_sha256':records[0]['sha256']},indent=2))
