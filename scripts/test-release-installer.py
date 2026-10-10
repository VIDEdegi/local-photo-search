"""QA product/registry/shortcuts only. Separate install and data directories."""
from contextlib import closing
import hashlib,json,os,sqlite3,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
test=root/'data/release-tests';destination=test/'installed-qa';data=test/'installer-data'
destination.mkdir(exist_ok=True);data.mkdir(exist_ok=True)
assert destination.is_relative_to(test) and destination.name=='installed-qa'
path=data/'index.sqlite3'
if not path.exists():
    with closing(sqlite3.connect((root/'data/ui-test/index.sqlite3').as_uri()+'?mode=ro',uri=True)) as old:
        with closing(sqlite3.connect(path)) as copied:old.backup(copied)
with closing(sqlite3.connect(path)) as db:
    assert db.execute('SELECT COUNT(*) FROM embeddings').fetchone()[0]>=4
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
before=hashlib.sha256(path.read_bytes()).hexdigest()
report={}
current=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))['version']
def install(version):
    package=test/'installers'/(version+'.exe')
    assert package.is_file()
    result=subprocess.run([str(package),'/S','/D='+str(destination)],timeout=180)
    assert result.returncode==0,result.returncode
    assert (destination/'embeddinggemma-media-search.exe').is_file()
    assert not list(destination.rglob('*.litertlm'))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
def uninstall():
    uninstaller=destination/'uninstall.exe';assert uninstaller.parent==destination
    result=subprocess.run([str(uninstaller),'/S','_?='+str(destination)],timeout=180);assert result.returncode==0
    end=time.monotonic()+30
    while (destination/'embeddinggemma-media-search.exe').exists() and time.monotonic()<end:time.sleep(.2)
    assert not (destination/'embeddinggemma-media-search.exe').exists()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
install('0.1.1');report['qa_old_install']=True
install(current);report['qa_upgrade']=True
install(current);report['qa_reinstall']=True
uninstall();report['qa_uninstall_keeps_separate_data']=True
install(current);report['qa_install_after_uninstall']=True
exe=destination/'embeddinggemma-media-search.exe'
before_exe=hashlib.sha256(exe.read_bytes()).hexdigest()
env=dict(os.environ,MEDIA_SEARCH_DATA=str(test/'installer-live-data'))
app=subprocess.Popen([str(exe)],env=env)
try:
    time.sleep(4);assert app.poll() is None,'Isolated QA app did not start'
    package=test/'installers'/(current+'.exe')
    result=subprocess.run([str(package),'/S','/D='+str(destination)],timeout=45)
    assert result.returncode!=0,'Installer accepted a running app'
    assert app.poll() is None,'Installer stopped the running app'
    assert hashlib.sha256(exe.read_bytes()).hexdigest()==before_exe
    result=subprocess.run([str(destination/'uninstall.exe'),'/S','_?='+str(destination)],timeout=45)
    assert result.returncode!=0,'Uninstaller accepted a running app'
    assert app.poll() is None and exe.is_file(),'Uninstaller modified the running app'
    report['running_app_install_refused']=True;report['running_app_uninstall_refused']=True
finally:
    if app.poll() is None:app.kill();app.wait(timeout=10)
report['qa_identity_only']=True;report['user_install_unchanged']=True
(test/'rc-audit').mkdir(exist_ok=True)
(test/'rc-audit/installer-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
