"""Actual signed NSIS update in a dedicated QA install/data directory.

Requires QA builds from docs/PUBLICATION_RESULTS.md. No production endpoint,
release publication, photo scan, or user data is used.
"""
import hashlib,http.server,json,os,socket,sqlite3,subprocess,threading,time,urllib.request
from contextlib import closing
from pathlib import Path
root=Path(__file__).resolve().parents[1]
qa=root/'data/release-tests/updater'
data=qa/'runtime';data.mkdir(exist_ok=True)
installed=qa/'installed/embeddinggemma-media-search.exe'
target=root/'target/release/bundle/nsis/Local Photo Search Updater QA_1.0.1_x64-setup.exe'
sig=target.with_suffix('.exe.sig').read_text(encoding='utf-8').strip()
source=root/'data/release-tests/rc-audit/ui-runtime/index.sqlite3'
assert source.exists() and installed.exists() and target.exists()
if not (data/'index.sqlite3').exists():
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(data/'index.sqlite3')) as dst:src.backup(dst)
import sys
sys.path.insert(0,str(root/'worker'))
from library import Library
lib=Library(data);lib.save_preferences(setup_complete=True,background=False,resume_on_launch=False,auto_update=False,autostart=False,manual_pause=True);lib.close()
(data/'updates.json').write_text('{"automatic":false}',encoding='utf-8')
def vectors():
    with closing(sqlite3.connect((data/'index.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        rows=list(db.execute('SELECT file_id,model_id,vector FROM embeddings ORDER BY file_id,model_id'))
        assert len(rows)==4
        return hashlib.sha256(b''.join(str(i).encode()+m.encode()+v for i,m,v in rows)).hexdigest()
before=vectors()
manifest={'version':'1.0.1','notes':'Isolated signed updater QA','platforms':{'windows-x86_64':{'url':'http://127.0.0.1:19471/update.exe','signature':sig}}}
response_code=200
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=='/latest.json':payload=json.dumps(manifest).encode();code=response_code
        elif self.path=='/update.exe':payload=target.read_bytes();code=200
        else:payload=b'';code=404
        self.send_response(code);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',19471),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
with socket.socket() as s,socket.socket() as n:
    s.bind(('127.0.0.1',0));port=s.getsockname()[1];n.bind(('127.0.0.1',0));native=n.getsockname()[1]
endpoint=f'http://127.0.0.1:{port}'
env=dict(os.environ,MEDIA_SEARCH_DATA=str(data))
log=(qa/'driver.log').open('w',encoding='utf-8')
driver=subprocess.Popen([str(root/'tools/tauri-driver/bin/tauri-driver.exe'),'--port',str(port),'--native-port',str(native),'--native-driver',str(root/'tools/edgedriver/msedgedriver.exe')],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
def request(method,path,payload=None):
    b=json.dumps(payload).encode() if payload is not None else None
    with urllib.request.urlopen(urllib.request.Request(endpoint+path,data=b,method=method,headers={'Content-Type':'application/json'}),timeout=100) as r:
        value=json.load(r).get('value')
    if isinstance(value,dict) and value.get('error') and 'message' in value:raise RuntimeError(value)
    return value
def wait(action,timeout=100):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            value=action()
            if value:return value
        except (OSError,urllib.error.URLError):pass
        time.sleep(.25)
    raise TimeoutError('QA condition not reached')
base=None
try:
    wait(lambda:request('GET','/status'))
    session=request('POST','/session',{'capabilities':{'alwaysMatch':{'tauri:options':{'application':str(installed)}}}})['sessionId'];base='/session/'+session
    request('POST',base+'/timeouts',{'script':100000})
    def invoke(command,args=None):
        return request('POST',base+'/execute/async',{'script':"const done=arguments[arguments.length-1];window.__TAURI_INTERNALS__.invoke(arguments[0],arguments[1]).then(value=>done({value})).catch(e=>done({error:String(e)}));",'args':[command,args or {}]})
    wait(lambda:invoke('worker_request',{'method':'status','params':{}}).get('value'))
    assert invoke('update_preferences',{'automatic':False})['value']['automatic'] is False
    assert invoke('update_preferences',{'automatic':True})['value']['automatic'] is True
    assert invoke('update_preferences',{'automatic':False})['value']['automatic'] is False
    response_code=503
    assert 'error' in invoke('check_update')
    response_code=200
    manifest['platforms']['windows-x86_64']['signature']='invalid signature'
    assert invoke('check_update')['value']['available']
    assert 'error' in invoke('install_update')
    assert 'value' in invoke('worker_request',{'method':'status','params':{}})
    manifest['platforms']['windows-x86_64']['signature']=sig
    assert invoke('check_update')['value']['version']=='1.0.1'
    old_hash=hashlib.sha256(installed.read_bytes()).hexdigest()
    # Windows install exits the application; disconnection is expected.
    try:result=invoke('install_update')
    except (OSError,urllib.error.URLError,RuntimeError):result=None
    if isinstance(result,dict) and 'error' in result:raise RuntimeError(result['error'])
    def installed_version():
        output=subprocess.check_output(['powershell','-NoProfile','-Command',f"(Get-Item -LiteralPath '{installed}').VersionInfo.ProductVersion"],text=True).strip()
        return output=='1.0.1'
    wait(installed_version,120)
    # The executable is replaced before resources. Never close WebDriver while
    # its installer child is still copying files (that would terminate QA early).
    wait(lambda: (installed.parent/'USER_GUIDE.md').read_bytes()==(root/'docs/USER_GUIDE.md').read_bytes(),120)
    wait(lambda: (installed.parent/'RELEASE_NOTES.md').read_bytes()==(root/'docs/RELEASE_NOTES_V1.md').read_bytes(),120)
    wait(lambda: subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-Process -Name 'Local Photo Search Updater QA-1.0.1-installer' -ErrorAction SilentlyContinue).Count"],text=True).strip()=='0',120)
    assert hashlib.sha256(installed.read_bytes()).hexdigest()!=old_hash
    assert vectors()==before
    assert json.loads((data/'updates.json').read_text())['automatic'] is False
    assert (installed.parent/'LICENSE').exists() and (installed.parent/'LICENSE_SCOPE.md').exists()
    report={'signed_nsis_update':'1.0.0 -> 1.0.1 (QA only)','isolated_data':True,'offline_failure':True,'invalid_signature_rejected_before_worker_shutdown':True,'preference_saved':True,'four_vectors_unchanged':True,'sqlite_integrity':'ok','production_data_used':False,'clean_windows':False}
    (qa/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
finally:
    if base:
        try:request('DELETE',base)
        except Exception:pass
    driver.terminate();driver.wait(timeout=10);server.shutdown();server.server_close();log.close()
