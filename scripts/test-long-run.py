"""2000 synthetic photos, real packaged GPU. No user library mutations."""
from contextlib import closing
import ctypes,hashlib,json,os,shutil,sqlite3,subprocess,time
from ctypes import wintypes
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'data/release-tests/long-run'
out.mkdir(exist_ok=False);photos=out/'photos';photos.mkdir();data=out/'index'
fixtures=[p for p in (root/'data/fixtures').rglob('*') if p.is_file()]
for i in range(2000):
    folder=photos/f'group-{i%16:02d}'/'nested';folder.mkdir(parents=True,exist_ok=True)
    source=fixtures[i%len(fixtures)];shutil.copy2(source,folder/f'photo-{i:04d}{source.suffix}')
(photos/'broken.jpg').write_bytes(b'not an image');(photos/'unsupported.png').write_bytes(b'not png')
def photo_hash():
    h=hashlib.sha256()
    for p in sorted(photos.rglob('*')):
        if p.is_file():h.update(str(p.relative_to(photos)).encode()+p.read_bytes())
    return h.hexdigest()
protected=photo_hash();report={'synthetic_photos':2000,'broken_photos':2,'source_hash_before':protected}
kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi')
kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
kernel.CloseHandle.argtypes=[wintypes.HANDLE]
class Memory(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in ['peak_rss','rss','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private']]
psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Memory),wintypes.DWORD]
peak=0
class Client:
    def __init__(self):
        self.log=(out/'worker.log').open('a',encoding='utf-8');self.id=0
        env=dict(os.environ,PATH=os.environ['SystemRoot']+'\\System32',PYTHONPATH='',PYTHONHOME='')
        self.p=subprocess.Popen([str(root/'dist-worker/media-search-worker/media-search-worker.exe'),'--data',str(data)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,encoding='utf-8',env=env)
    def call(self,method,params={}):
        global peak
        handle=kernel.OpenProcess(0x410,False,self.p.pid)
        if handle:
            m=Memory();m.cb=ctypes.sizeof(m)
            if psapi.GetProcessMemoryInfo(handle,ctypes.byref(m),m.cb):peak=max(peak,m.rss)
            kernel.CloseHandle(handle)
        self.id+=1;self.p.stdin.write(json.dumps({'version':1,'id':self.id,'method':method,'params':params})+'\n');self.p.stdin.flush();reply=json.loads(self.p.stdout.readline())
        if 'error' in reply:raise RuntimeError(reply['error'])
        return reply['result']
    def close(self,crash=False):
        if crash:self.p.kill()
        else:self.call('shutdown')
        self.p.wait(timeout=30);self.log.close();self.p.stdin.close();self.p.stdout.close()
def wait(client,done=None):
    end=time.monotonic()+1500
    while time.monotonic()<end:
        status=client.call('status')
        (out/'progress.json').write_text(json.dumps({'phase':status['progress']['phase'],'processed':status['progress']['processed'],'jobs':status['jobs'],'elapsed_seconds':round(time.monotonic()-started,1),'peak_rss_mib':round(peak/1024**2,1)}),encoding='utf-8')
        if done and status['jobs'].get('done',0)>=done:return status
        if not done and not status['running']:return status
        if status['progress']['last_error'] and not status['running']:raise RuntimeError(status)
        time.sleep(.5)
    raise TimeoutError('Long-run timeout')
def vectors():
    with closing(sqlite3.connect((data/'index.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
        return {i:hashlib.sha256(v).hexdigest() for i,v in db.execute('SELECT file_id,vector FROM embeddings')}
client=None;started=time.monotonic()
try:
    client=Client();client.call('configure',{'model_path':str(root/'data/models/embeddinggemma-2-740m.litertlm'),'backend':'gpu'})
    client.call('add_folder',{'path':str(photos)});client.call('add_folder',{'path':str(photos/'group-00')})
    client.call('start');wait(client,64);client.call('pause');wait(client);saved=vectors();report['pause_kept']=len(saved);client.close()
    client=Client();client.call('start');wait(client,128);saved=vectors();report['crash_kept']=len(saved);client.close(crash=True)
    client=Client();client.call('start');final=wait(client)
    assert final['jobs'].get('done')==2000 and final['jobs'].get('error')==2,final
    assert final['total']==2002,final
    current=vectors();assert all(current[i]==h for i,h in saved.items())
    client.call('start');again=wait(client);assert again['progress']['processed']==0,again
    assert photo_hash()==protected
    with closing(sqlite3.connect((data/'index.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not db.execute('PRAGMA foreign_key_check').fetchone()
    report.update(seconds=round(time.monotonic()-started,2),peak_rss_mib=round(peak/1024**2,2),done=2000,errors=2,overlapping_folders_no_duplicate=True,unchanged_reprocessed=0,sqlite_integrity='ok',cache_bytes=final['runtime_cache_bytes'],source_hash_after=photo_hash(),saved_vectors_preserved=True)
    (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
finally:
    if client and client.p.poll() is None:client.close()
