"""Real NSIS failure paths with injected Restart Manager errors; QA only."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'data/release-tests/installers'
version=json.loads((root/'src-tauri/tauri.conf.json').read_text())['version']
source=(folder/(version+'.nsi')).read_text(encoding='utf-8')
destination=root/'data/release-tests/installed-qa'
application=destination/'embeddinggemma-media-search.exe'
assert application.is_file(),'Run the isolated installer cycle first'
before=hashlib.sha256(application.read_bytes()).hexdigest()
hooks=root/'src-tauri/windows/hooks.nsh';original=hooks.read_text(encoding='utf-8')
assert '!macroundef CheckIfAppIsRunning' in original
report={}
with tempfile.TemporaryDirectory(prefix='installer-failures-',dir=root/'tmp') as temporary:
    work=Path(temporary).resolve();assert work.is_relative_to(root/'tmp')
    for name,body in (
        ('session_unavailable','!macroundef RestartManager_StartSession\n!macro RestartManager_StartSession output\nStrCpy ${output} ""\n!macroend\n'),
        ('registration_failed','!macroundef RestartManager_RegisterFile\n!macro RestartManager_RegisterFile handle path\nStrCpy $0 5\n!macroend\n'),
        ('process_list_failed',None)):
        hook=work/(name+'.nsh')
        if body is not None:
            hook.write_text(f'!include "{hooks}"\n'+body,encoding='utf-8')
        else:
            actual="System::Call 'RSTRTMGR::RmGetList(p R0, *i .r1, *i .r2, p 0, *i .r3) i .r0'"
            assert actual in original
            text=original.replace(actual,'StrCpy $0 5').replace('!define LPS_HOOK_DIRECTORY "${__FILEDIR__}"',f'!define LPS_HOOK_DIRECTORY "{hooks.parent}"')
            hook.write_text(text,encoding='utf-8')
        executable=work/(name+'.exe');script=work/(name+'.nsi')
        text=source.replace(str(hooks),str(hook)).replace('SetCompressor /SOLID "lzma"','SetCompress off').replace(str(folder/(version+'.exe')),str(executable))
        script.write_text(text,encoding='utf-8')
        subprocess.run([str(root/'target/.tauri/NSIS/makensis.exe'),'/V1','/NOCD',str(script)],cwd=root/'target/release/nsis/x64',timeout=120,check=True)
        result=subprocess.run([str(executable),'/S','/D='+str(destination)],timeout=45)
        assert result.returncode!=0,(name,'Failure was accepted')
        assert hashlib.sha256(application.read_bytes()).hexdigest()==before,name
        report[name]={'refused':True,'installed_executable_unchanged':True,'exit_code':result.returncode}
(root/'data/release-tests/rc-audit/installer-failures.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
