"""Verify native OS launch requests for a registered fixture (no source writes)."""
import urllib.request,json,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];endpoint='http://127.0.0.1:4444'
def req(method,path,data=None):
    request=urllib.request.Request(endpoint+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=150) as response:value=json.load(response)['value']
    if isinstance(value,dict) and value.get('error'):raise RuntimeError(value)
    return value
session=req('POST','/session',{'capabilities':{'alwaysMatch':{'tauri:options':{'application':str(root/'app/embeddinggemma-media-search.exe')}}}})['sessionId'];base='/session/'+session
try:
    req('POST',base+'/timeouts',{'script':120000})
    def invoke(command,args):
        result=req('POST',base+'/execute/async',{'script':"const done=arguments[arguments.length-1];window.__TAURI_INTERNALS__.invoke(arguments[0],arguments[1]).then(result=>done({result})).catch(error=>done({error:String(error)}));",'args':[command,args]})
        if 'error' in result:raise RuntimeError(result)
        return result['result']
    files=invoke('worker_request',{'method':'search','params':{'filename':'coast'}})['items'];assert len(files)==1
    id=files[0]['id']
    invoke('open_media',{'id':id,'reveal':False});invoke('open_media',{'id':id,'reveal':True})
    report={'registered_original_os_launch_accepted':True,'explorer_reveal_launch_accepted':True,'external_viewer_visual_verification':False}
    (root/'data/native-actions-test-results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:req('DELETE',base)
