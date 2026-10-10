"""Real packaged app/WebView2/IPC in driver-inherited release-tests/ui data."""
import base64,json,os,shutil,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'data/release-tests'
endpoint=os.environ.get('MEDIA_SEARCH_TEST_ENDPOINT','http://127.0.0.1:4444')
def request(method,path,payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    with urllib.request.urlopen(urllib.request.Request(endpoint+path,data=data,method=method,headers={'Content-Type':'application/json'}),timeout=150) as response:value=json.load(response).get('value')
    if isinstance(value,dict) and value.get('error'):raise RuntimeError(value)
    return value
def wait(action,timeout=120):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        value=action()
        if value:return value
        time.sleep(.25)
    raise TimeoutError('Condition did not become true')
exe=os.environ.get('MEDIA_SEARCH_TEST_EXE',str(root/'target/release/embeddinggemma-media-search.exe'))
print('Creating WebView2 session',flush=True)
session=request('POST','/session',{'capabilities':{'alwaysMatch':{'tauri:options':{'application':exe}}}})['sessionId'];base='/session/'+session
(out/'desktop-session.txt').write_text(session,encoding='utf-8')
print('WebView2 session created',flush=True)
request('POST',base+'/timeouts',{'script':120000})
def js(script,args=[]):return request('POST',base+'/execute/sync',{'script':script,'args':args})
def native(command,params={}):
    r=request('POST',base+'/execute/async',{'script':"const done=arguments[arguments.length-1];window.__TAURI_INTERNALS__.invoke(arguments[0],arguments[1]).then(result=>done({result})).catch(e=>done({error:String(e)}));",'args':[command,params]})
    if 'error' in r:raise RuntimeError(r['error'])
    return r['result']
def rpc(method,params={}):return native('worker_request',{'method':method,'params':params})
prefix="const a=document.querySelector('media-search-app'),c=a?.shadowRoot?.querySelector('release-controls[mode=assistant]');"
def advance():js(prefix+"c.shadowRoot.querySelector('#wizard .dialog-actions .primary').click();")
report={}
try:
    wait(lambda:js(prefix+"return !!c?.shadowRoot?.querySelector('#wizard')?.open"))
    status=rpc('status');assert 'release-tests' in status['data_path'];assert not status['preferences']['setup_complete']
    print('First-run wizard visible',flush=True)
    report['first_run_wizard']=True
    report['setup_resume_step']=status['preferences']['setup_step']
    assert js(prefix+"return c.step")==status['preferences']['setup_step']
    for step in range(status['preferences']['setup_step']-1,-1,-1):
        js(prefix+"c.next(-1);");wait(lambda:rpc('status')['preferences']['setup_step']==step)
    advance();wait(lambda:rpc('status')['preferences']['setup_step']==1)
    environment=rpc('environment');assert environment['python_bundled'] and environment['runtime']=={'litert-lm-api':'0.18.0','Pillow':'12.3.0'},environment
    report['packaged_runtime']=environment
    advance();wait(lambda:rpc('status')['preferences']['setup_step']==2)
    request('POST',base+'/refresh',{})
    wait(lambda:js(prefix+"return c?.step===2 && c.shadowRoot.querySelector('#wizard').open"))
    report['wizard_step_persisted_on_reload']=True
    rpc('configure',{'model_path':str(root/'data/models/embeddinggemma-2-740m.litertlm'),'backend':'gpu'})
    js('document.querySelector("media-search-app").refresh()')
    print('Diagnosing packaged GPU',flush=True)
    js(prefix+"c.diagnose();")
    wait(lambda:js(prefix+"return c.diagnosticOK && !c.working"))
    report['gpu_probe']={'ok':True,'message':js(prefix+"return c.diagnostic")}
    print('GPU diagnostic completed',flush=True)
    advance();wait(lambda:rpc('status')['preferences']['setup_step']==3)
    advance();wait(lambda:rpc('status')['preferences']['setup_step']==4)
    photos=out/'background-photos';photos.mkdir(exist_ok=True)
    fixture=list((root/'data/fixtures').rglob('*'));fixture=[p for p in fixture if p.is_file()]
    for i in range(24):
        target=photos/f'photo-{i:02d}{fixture[i%len(fixture)].suffix}'
        if not target.exists():shutil.copy2(fixture[i%len(fixture)],target)
    rpc('add_folder',{'path':str(photos)})
    advance();wait(lambda:rpc('status')['preferences']['setup_step']==5)
    native('desktop_preferences',{'preferences':{'background':True,'resume_on_launch':True,'low_load':True}})
    advance();wait(lambda:rpc('status')['preferences']['setup_step']==6)
    # Start through real IPC, then close the actual native window into the tray.
    print('Starting background/close test',flush=True)
    rpc('start');native('desktop_action',{'action':'close'})
    wait(lambda:native('plugin:window|is_visible',{'label':'main'}) is False)
    before=rpc('status')['progress']['processed'];time.sleep(3);after=rpc('status')
    assert after['running'] or after['jobs'].get('done')==24
    wait(lambda:rpc('status')['progress']['processed']>before)
    report['close_keeps_worker_and_indexing']=True
    rpc('pause');wait(lambda:not rpc('status')['running']);saved=rpc('status')['jobs'].get('done',0)
    assert saved>0 and rpc('status')['preferences']['manual_pause']
    rpc('start');wait(lambda:not rpc('status')['running']);assert rpc('status')['jobs'].get('done')==24
    report['pause_resume_saved']=saved
    native('desktop_action',{'action':'show'});assert native('plugin:window|is_visible',{'label':'main'})
    rpc('preferences',{'setup_complete':True,'setup_step':7,'background':False,'low_load':False})
    js(prefix+"c.shadowRoot.querySelector('#wizard').close();a.refresh();")
    js(prefix+"c.openHelp();")
    wait(lambda:js(prefix+"return c.shadowRoot.querySelector('#help').open"))
    (out/'help.png').write_bytes(base64.b64decode(request('GET',base+'/screenshot')))
    js(prefix+"c.shadowRoot.querySelector('#help').close();a.settings();")
    wait(lambda:js("return document.querySelector('media-search-app').shadowRoot.querySelector('#settings').open"))
    (out/'settings.png').write_bytes(base64.b64decode(request('GET',base+'/screenshot')))
    report['help_and_settings']=True
    # Model/cache/index are not reset by graceful shutdown.
    rpc('pause');report['indexed_photos']=rpc('status')['jobs']['done']
    report['complete']=True
    (out/'desktop-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
finally:
    try:request('DELETE',base)
    except Exception:pass
