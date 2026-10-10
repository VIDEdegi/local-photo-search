"""Install / reinstall / uninstall only this test app under the project root."""
from pathlib import Path
import subprocess,sqlite3,hashlib,json,time,os
root=Path(__file__).resolve().parents[1]
destination=(root/'app').resolve()
assert destination==Path('E:/EmbeddingGemmaMediaSearch/app').resolve()
installer=root/'target/release/bundle/nsis/Local Photo Search_0.1.0_x64-setup.exe'
db_path=root/'data/ui-test/index.sqlite3'
def snapshot():
    with sqlite3.connect(db_path) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        return {str(id):hashlib.sha256(vector).hexdigest() for id,vector in db.execute('SELECT file_id,vector FROM embeddings')}
def install():
    result=subprocess.run([str(installer),'/S','/D='+str(destination)],timeout=150)
    assert result.returncode==0,result.returncode
    assert (destination/'embeddinggemma-media-search.exe').is_file()
    assert (destination/'worker/media-search-worker.exe').is_file()
    assert not list(destination.rglob('*.litertlm'))
    assert (destination/'licenses/python/CPython').is_dir()
    return result.returncode
before=snapshot();assert len(before)==4
install();assert snapshot()==before
print('Installed / upgraded with model excluded and vectors preserved',flush=True)
uninstaller=(destination/'uninstall.exe').resolve(strict=True)
assert uninstaller.parent==destination
result=subprocess.run([str(uninstaller),'/S','_?='+str(destination)],timeout=150);assert result.returncode==0
# NSIS uninstaller can delegate to a temporary helper.
deadline=time.monotonic()+30
while (destination/'embeddinggemma-media-search.exe').exists() and time.monotonic()<deadline:time.sleep(.2)
assert not (destination/'embeddinggemma-media-search.exe').exists()
assert snapshot()==before
install();assert snapshot()==before
exe=destination/'embeddinggemma-media-search.exe'
env=dict(os.environ,MEDIA_SEARCH_TEST_EXE=str(exe))
for script in ['test-lifecycle.py','test-desktop.py']:
    result=subprocess.run([os.sys.executable,str(root/'scripts'/script)],env=env,timeout=180)
    assert result.returncode==0,script
assert snapshot()==before
report={'install':True,'same_version_reinstall':True,'uninstall':True,'reinstall_after_uninstall':True,'vectors_preserved':len(before),'model_not_bundled':True,'installed_exe':str(exe),'installed_webview2_flow':True}
(root/'data/installer-test-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
