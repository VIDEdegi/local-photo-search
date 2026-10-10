"""Real installed QA app, keyboard events, isolated Worker crash/restart; no user data."""
from contextlib import closing
import ctypes, hashlib, json, os, sqlite3, subprocess, time, urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1];out=root/'data/release-tests'
exe=Path(os.environ.get('MEDIA_SEARCH_TEST_EXE',str(root/'data/release-tests/installed-qa/embeddinggemma-media-search.exe')))
endpoint=os.environ.get('MEDIA_SEARCH_TEST_ENDPOINT','http://127.0.0.1:4448')
def request(method,path,payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    with urllib.request.urlopen(urllib.request.Request(endpoint+path,data=data,method=method,headers={'Content-Type':'application/json'}),timeout=150) as response:
        value=json.load(response)['value']
    if isinstance(value,dict) and value.get('error'):raise RuntimeError(value)
    return value
session=request('POST','/session',{'capabilities':{'alwaysMatch':{'tauri:options':{'application':str(exe)}}}})['sessionId'];base='/session/'+session
request('POST',base+'/timeouts',{'script':120000})
def js(script):return request('POST',base+'/execute/sync',{'script':script,'args':[]})
def invoke(method,params):
    return request('POST',base+'/execute/async',{'script':"const done=arguments[arguments.length-1];window.__TAURI_INTERNALS__.invoke(arguments[0],arguments[1]).then(result=>done({result})).catch(e=>done({rpc_error:String(e)}));",'args':[method,params]})
def rpc(method,params={}):
    result=invoke('worker_request',{'method':method,'params':params})
    if 'rpc_error' in result:raise RuntimeError(result['rpc_error'])
    return result['result']
def wait(action):
    end=time.monotonic()+60
    while time.monotonic()<end:
        result=action()
        if result:return result
        time.sleep(.2)
    raise TimeoutError('Recovery condition timed out')
def processes():
    shell=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    result=subprocess.run([str(shell),'-NoProfile','-Command',"Get-CimInstance Win32_Process -Filter \"Name='embeddinggemma-media-search.exe' OR Name='media-search-worker.exe'\" | Select-Object ProcessId,ParentProcessId,ExecutablePath | ConvertTo-Json -Compress"],capture_output=True,text=True,creationflags=0x08000000,timeout=30,check=True)
    value=json.loads(result.stdout or '[]');return value if isinstance(value,list) else [value]
def vector_hash(path):
    with closing(sqlite3.connect((path/'index.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
        h=hashlib.sha256()
        for i,m,v in db.execute('SELECT file_id,model_id,vector FROM embeddings ORDER BY file_id,model_id'):h.update(str(i).encode()+m.encode()+v)
        return h.hexdigest()
def keys(sequence):
    request('POST',base+'/actions',{'actions':[{'type':'key','id':'keyboard','actions':[{'type':action,'value':value} for action,value in sequence]}]})
report={}
try:
    wait(lambda:js("return !!document.querySelector('media-search-app')?.shadowRoot?.querySelector('#query')"))
    status=rpc('status');data=Path(status['data_path']).resolve();assert data.is_relative_to(out) and status['jobs'].get('done')==4,status
    protected=vector_hash(data)
    js("const a=document.querySelector('media-search-app');a.shadowRoot.querySelector('release-controls[mode=assistant]')?.shadowRoot.querySelector('#wizard')?.close()")
    keys([('keyDown','\ue009'),('keyDown','k'),('keyUp','k'),('keyUp','\ue009')])
    assert js("const r=document.querySelector('media-search-app').shadowRoot;return r.activeElement===r.querySelector('#query')")
    report['ctrl_k_focus']=True
    keys([('keyDown','\ue031'),('keyUp','\ue031')])
    wait(lambda:js("return document.querySelector('media-search-app').shadowRoot.querySelector('release-controls[mode=assistant]').shadowRoot.querySelector('#help').open"))
    keys([('keyDown','\ue00c'),('keyUp','\ue00c')])
    wait(lambda:js("return !document.querySelector('media-search-app').shadowRoot.querySelector('release-controls[mode=assistant]').shadowRoot.querySelector('#help').open"))
    report['f1_help_escape_close']=True
    rows=processes();apps=[r for r in rows if r['ExecutablePath'] and Path(r['ExecutablePath'])==exe]
    assert len(apps)==1,apps
    app_pid=apps[0]['ProcessId'];workers=[r for r in rows if r['ParentProcessId']==app_pid and Path(r['ExecutablePath']).name=='media-search-worker.exe']
    assert len(workers)==1,workers
    worker_pid=workers[0]['ProcessId']
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];kernel.OpenProcess.restype=ctypes.c_void_p
    kernel.TerminateProcess.argtypes=[ctypes.c_void_p,ctypes.c_uint32];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    handle=kernel.OpenProcess(1,False,worker_pid);assert handle
    try:assert kernel.TerminateProcess(handle,1)
    finally:kernel.CloseHandle(handle)
    time.sleep(.5)
    error=invoke('worker_request',{'method':'status','params':{}});assert 'rpc_error' in error,error
    assert js("return !!document.querySelector('media-search-app')?.shadowRoot?.querySelector('#query')")
    report['worker_crash_leaves_app_alive']=True;report['friendly_worker_error']=error['rpc_error']
    result=invoke('desktop_action',{'action':'restart_worker'});assert 'result' in result,result
    assert rpc('status')['jobs'].get('done')==4
    assert rpc('environment')['runtime']['Pillow']=='12.3.0'
    assert rpc('search',{'text':'海辺の風景'})['items'][0]['name']=='coast.png'
    assert vector_hash(data)==protected
    report['native_restart_restores_japanese_search']=True;report['saved_vectors_preserved']=True
    rpc('preferences',{'setup_step':4,'setup_complete':False,'background':False})
    js("setTimeout(()=>window.__TAURI_INTERNALS__.invoke('desktop_action',{action:'close'}),20);return true")
    wait(lambda:not any(r['ProcessId']==app_pid for r in processes()))
    try:request('DELETE',base)
    except Exception:pass
    session=request('POST','/session',{'capabilities':{'alwaysMatch':{'tauri:options':{'application':str(exe)}}}})['sessionId'];base='/session/'+session
    request('POST',base+'/timeouts',{'script':120000})
    wait(lambda:js("const a=document.querySelector('media-search-app'),c=a?.shadowRoot?.querySelector('release-controls[mode=assistant]');return c?.step===4 && c.shadowRoot.querySelector('#wizard').open"))
    assert Path(rpc('status')['data_path']).resolve()==data
    assert vector_hash(data)==protected
    report['wizard_resume_after_native_exit_and_relaunch']=4
    rpc('preferences',{'setup_step':7,'setup_complete':True})
    (out/'recovery-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
finally:
    request('DELETE',base)
