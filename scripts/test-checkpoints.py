"""Crash and resume checks using the actual packaged Worker and GPU model."""
import subprocess,json,time,tempfile,shutil,sqlite3,hashlib,atexit
clients=[]
def cleanup():
    for client in clients:
        if client.p.poll() is None:client.p.kill();client.p.wait(timeout=10)
atexit.register(cleanup)
from pathlib import Path
root=Path(__file__).resolve().parents[1]
exe=root/'dist-worker/media-search-worker/media-search-worker.exe'

class Client:
    def __init__(self,data):
        self.log=(root/'data/checkpoint-worker.log').open('a',encoding='utf-8')
        self.p=subprocess.Popen([str(exe),'--data',str(data)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,encoding='utf-8');self.id=0;clients.append(self)
    def call(self,method,params={}):
        self.id+=1;self.p.stdin.write(json.dumps({'version':1,'id':self.id,'method':method,'params':params})+'\n');self.p.stdin.flush();line=self.p.stdout.readline()
        if not line:raise RuntimeError('Worker unexpectedly exited')
        reply=json.loads(line)
        if 'error' in reply:raise RuntimeError(reply['error'])
        return reply['result']
    def stop(self,crash=False):
        if crash:self.p.kill()
        else:self.call('shutdown')
        self.p.wait(timeout=30);self.log.close()

def wait(client,condition):
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        status=client.call('status')
        if condition(status):return status
        if status['progress']['phase']=='error':raise RuntimeError(status)
        time.sleep(.1)
    raise TimeoutError(status)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
report={}
with tempfile.TemporaryDirectory(dir=root/'tmp',ignore_cleanup_errors=True) as temp:
    data=Path(temp)/'index';photos=Path(temp)/'日本語の写真';photos.mkdir()
    samples=list((root/'data/fixtures').rglob('*'))
    samples=[p for p in samples if p.is_file()]
    for n in range(24):shutil.copyfile(samples[n%4],photos/f'fixture-{n:02}{samples[n%4].suffix}')
    original={p.name:sha(p) for p in photos.iterdir()}
    client=Client(data);client.call('configure',{'model_path':str(root/'data/models/embeddinggemma-2-740m.litertlm'),'backend':'gpu'});client.call('add_folder',{'path':str(photos)});client.call('start')
    state=wait(client,lambda s:s['jobs'].get('done',0)>=2 and s['running'])
    client.call('pause');state=wait(client,lambda s:not s['running']);saved=state['jobs']['done'];assert 0<saved<24,state
    report['pause_saved']=saved;client.stop()
    client=Client(data);assert client.call('status')['jobs']['done']==saved
    client.call('start');state=wait(client,lambda s:s['jobs'].get('done',0)>saved and s['jobs'].get('processing',0)==1)
    with sqlite3.connect(data/'index.sqlite3') as db:
        saved_vectors={id:hashlib.sha256(vector).hexdigest() for id,vector in db.execute('SELECT file_id,vector FROM embeddings')}
    client.stop(crash=True)
    client=Client(data);assert not client.call('status')['jobs'].get('processing')
    client.call('start');state=wait(client,lambda s:not s['running']);assert state['jobs']['done']==24,state
    with sqlite3.connect(data/'index.sqlite3') as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        vectors={id:hashlib.sha256(vector).hexdigest() for id,vector in db.execute('SELECT file_id,vector FROM embeddings')}
        assert all(vectors[id]==value for id,value in saved_vectors.items())
    report['crash_resume_preserved_vectors']=len(saved_vectors);report['resumed_total']=24;report['sqlite_integrity']='ok'
    # GPU -> CPU must reuse compatible embeddings, not duplicate them.
    client.call('configure',{'model_path':str(root/'data/models/embeddinggemma-2-740m.litertlm'),'backend':'cpu'});client.call('search',{'text':'赤いりんご'});client.call('start');state=wait(client,lambda s:not s['running']);assert state['progress']['processed']==0,state
    with sqlite3.connect(data/'index.sqlite3') as db:
        assert db.execute('SELECT COUNT(*) FROM embeddings').fetchone()[0]==24
        assert db.execute('SELECT COUNT(*) FROM models').fetchone()[0]==1
    report['cpu_gpu_reused_same_profile']=True
    assert original=={p.name:sha(p) for p in photos.iterdir()};report['source_hashes_unchanged']=True
    client.stop()
(root/'data/checkpoint-test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
