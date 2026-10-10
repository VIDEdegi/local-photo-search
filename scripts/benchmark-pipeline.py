"""Read already-indexed photos; write ONLY isolated audit DB/cache. Never resume user jobs."""
import argparse,collections,ctypes,hashlib,io,json,os,shutil,sqlite3,statistics,subprocess,sys,threading,time,queue
from array import array
from pathlib import Path
from ctypes import wintypes
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--label',required=True);parser.add_argument('--count',type=int,default=24);parser.add_argument('--runs',type=int,default=3);parser.add_argument('--variant',choices=['baseline','paired','prefetch','production'],default='production');parser.add_argument('--worker-ref');args=parser.parse_args()
if args.variant!='production' and not args.worker_ref:parser.error('Baseline/prototype variants require --worker-ref e9bb9ea.')
assert args.label.isidentifier() and 2<=args.count<=1024 and args.runs>=1
out=root/'data/performance-audit';out.mkdir(exist_ok=True)
worker=root/'worker'
if args.worker_ref:
    worker=root/'data/performance-audit'/(args.label+'_worker');worker.mkdir(exist_ok=False)
    for name in ('ai.py','database.py','library.py','runtime_cache.py','prefetch.py'):
        source_file=subprocess.run(['git','show',args.worker_ref+':worker/'+name],cwd=root,capture_output=True)
        if source_file.returncode and name=='prefetch.py':continue
        source_file.check_returncode();(worker/name).write_bytes(source_file.stdout)
sys.path.insert(0,str(worker))
import library,ai
from runtime_cache import RuntimeCache
out=root/'data/performance-audit';out.mkdir(exist_ok=True)
source=sqlite3.connect((root/'data/index.sqlite3').as_uri()+'?mode=ro',uri=True);source.row_factory=sqlite3.Row
active=source.execute("SELECT value FROM settings WHERE key='active_model'").fetchone()[0]
count=source.execute('SELECT COUNT(*) FROM embeddings WHERE model_id=?',(active,)).fetchone()[0]
assert count>=2,'At least two already-indexed photos are required.'
selected=min(args.count,count);ranks={round(i*(count-1)/(selected-1)) for i in range(selected)}
rows=[row for i,row in enumerate(source.execute('SELECT f.*,e.vector,e.model_id FROM files f JOIN embeddings e ON e.file_id=f.id WHERE e.model_id=? ORDER BY f.id',(active,))) if i in ranks]
# Aggregate hash detects any change in the original saved embeddings without exposing paths.
def original_hash():
    digest=hashlib.sha256()
    for r in source.execute('SELECT file_id,model_id,vector FROM embeddings ORDER BY file_id,model_id'):digest.update(str(r[0]).encode()+r[1].encode()+r[2])
    return digest.hexdigest()
protected=original_hash();config=source.execute("SELECT value FROM settings WHERE key='config'").fetchone()
model=Path(json.loads(config[0])['model_path']) if config else root/'data/models/embeddinggemma-2-740m.litertlm'
sha=source.execute('SELECT sha256 FROM models WHERE id=?',(active,)).fetchone()[0]
cache=out/'runtime-cache'/sha
if not cache.exists():shutil.copytree(root/'data/runtime-cache'/sha,cache,copy_function=shutil.copy2)
# Never overwrite a prior run DB.
data=out/args.label;data.mkdir(exist_ok=False)
lib=library.Library(data);lib.runtime_cache=RuntimeCache(out);lib.configure(str(model),'gpu')
model_row=source.execute('SELECT * FROM models WHERE id=?',(rows[0]['model_id'],)).fetchone()
with lib.db:
    lib.db.execute('INSERT INTO models VALUES(?,?,?,?,?,?,?,?)',tuple(model_row))
    lib.db.execute("INSERT INTO folders(id,path,status) VALUES(1,?,'ready')",(str(Path(rows[0]['path']).parent),))
    cols=[r[1] for r in lib.db.execute('PRAGMA table_info(files)')]
    for row in rows:
        lib.db.execute('INSERT INTO files('+','.join(cols)+') VALUES('+','.join('?' for _ in cols)+')',tuple(row[key] for key in cols))
        lib.db.execute("INSERT INTO folder_files VALUES(1,?,'benchmark')",(row['id'],))
        lib.db.execute("INSERT INTO jobs(file_id,model_id,state) VALUES(?,?,'pending')",(row['id'],row['model_id']))
lib._scan=lambda _:None
samples=collections.defaultdict(list)
class DBProxy:
    def __init__(self,db):self.db=db
    def __getattr__(self,name):return getattr(self.db,name)
    def execute(self,*a,**kw):
        t=time.perf_counter()
        try:return self.db.execute(*a,**kw)
        finally:samples['sqlite_sql'].append(time.perf_counter()-t)
    def __enter__(self):return self.db.__enter__()
    def __exit__(self,*args):
        t=time.perf_counter()
        try:return self.db.__exit__(*args)
        finally:samples['sqlite_commit'].append(time.perf_counter()-t)
lib.db=DBProxy(lib.db)
original_prepare=library.prepare_image
if hasattr(library,'prepare_index_image'):
    original_pair=library.prepare_index_image
    def paired(*a,**kw):
        t=time.perf_counter()
        try:return original_pair(*a,**kw)
        finally:samples['prepare_pair'].append(time.perf_counter()-t)
    library.prepare_index_image=paired
else:
    def prepared(path,edge=1024):
        t=time.perf_counter()
        try:return original_prepare(path,edge)
        finally:samples['prepare_ai' if edge==1024 else 'prepare_thumbnail'].append(time.perf_counter()-t)
    library.prepare_image=prepared
# Prototypes affect ONLY this process and isolated index, not application code.
if args.variant in ('paired','prefetch'):
    from PIL import Image,ImageOps
    def pair(path):
        with Image.open(path) as source:
            rgb=ImageOps.exif_transpose(source).convert('RGB')
            outputs=[]
            for edge in (1024,320):
                image=rgb.copy();image.thumbnail((edge,edge));buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=95);outputs.append(buffer.getvalue())
            return outputs
    for row in rows:
        a,b=pair(Path(row['path']))
        assert a==original_prepare(Path(row['path']),1024) and b==original_prepare(Path(row['path']),320)
    pending_thumbnail={};prefetch_state={}
    def prototype_prepare(path,edge=1024):
        if edge==320:return pending_thumbnail.pop(str(path))
        t=time.perf_counter()
        if args.variant=='paired':
            a,b=pair(path);samples['prepare_pair'].append(time.perf_counter()-t)
        else:
            name,a,b,error=prefetch_state['queue'].get()
            assert name==str(path),(name,str(path))
            if error:raise error
            samples['prefetch_wait'].append(time.perf_counter()-t)
        pending_thumbnail[str(path)]=b
        return a
    library.prepare_image=prototype_prepare
    if args.variant=='prefetch':
        def start_prefetch(_):
            work_queue=queue.Queue(maxsize=2);prefetch_state['queue']=work_queue
            def produce():
                for row in rows:
                    path=Path(row['path']);t=time.perf_counter();error=None;a=b=None
                    try:a,b=pair(path)
                    except Exception as exc:error=exc
                    samples['prepare_pair'].append(time.perf_counter()-t)
                    work_queue.put((str(path),a,b,error))
            thread=threading.Thread(target=produce,daemon=True);thread.start();prefetch_state['thread']=thread
        lib._scan=start_prefetch
kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=wintypes.HANDLE
class Memory(ctypes.Structure):
    _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in ['peak_rss','rss','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private']]
psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Memory),wintypes.DWORD]
monitor_stop=threading.Event();memory_samples=[];gpu_samples=[]
def memory_monitor():
    while not monitor_stop.wait(.1):
        m=Memory();m.cb=ctypes.sizeof(m)
        if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(m),m.cb):memory_samples.append({'rss':m.rss,'private':m.private})
threading.Thread(target=memory_monitor,daemon=True).start()
gpu=None
try:
    gpu=subprocess.Popen(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,temperature.gpu','--format=csv,noheader,nounits','--loop-ms=200'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,creationflags=0x08000000)
    def gpu_monitor():
        for line in gpu.stdout:
            try:gpu_samples.append([float(x.strip()) for x in line.split(',')])
            except ValueError:pass
    threading.Thread(target=gpu_monitor,daemon=True).start()
except FileNotFoundError:pass
report={'label':args.label,'variant':args.variant,'worker_ref':args.worker_ref,'count':len(rows),'runs':[],'original_vector_hash_before':protected}
def cache_state():return {str(p.relative_to(out/'runtime-cache')):p.stat().st_size for p in lib.runtime_cache.files()}
report['cache_before']=cache_state()
t=time.perf_counter();lib.ensure_engine();report['load_and_initial_text_seconds']=time.perf_counter()-t
original_image=lib.engine.image
def inference(data):
    t=time.perf_counter()
    try:return original_image(data)
    finally:samples['ai_call'].append(time.perf_counter()-t)
lib.engine.image=inference
# One warmup avoids conflating first request compilation with steady-state throughput.
lib.engine.image(ai.prepare_image(Path(rows[0]['path'])))
report['cache_after_first_image']=cache_state()
for iteration in range(args.runs):
    with lib.db:lib.db.execute("UPDATE jobs SET state='pending',error=NULL")
    samples.clear();memory_samples.clear();gpu_samples.clear();cpu=time.process_time();t=time.perf_counter()
    lib.start();lib.thread.join(timeout=max(180,len(rows)*2))
    assert not lib.thread.is_alive(),lib.status()
    elapsed=time.perf_counter()-t
    assert not lib.progress['last_error'],lib.status()
    assert lib.progress['processed']==len(rows),lib.status()
    run={'seconds':elapsed,'images_per_second':len(rows)/elapsed,'cpu_seconds':time.process_time()-cpu,'stages':{name:{'total_seconds':sum(values),'calls':len(values),'mean_ms':statistics.mean(values)*1000,'p95_ms':sorted(values)[min(len(values)-1,int(.95*len(values)))]*1000} for name,values in samples.items()},'peak_rss_bytes':max((m['rss'] for m in memory_samples),default=0),'peak_private_bytes':max((m['private'] for m in memory_samples),default=0),'gpu_total_memory_mib_max':max((g[1] for g in gpu_samples),default=None),'gpu_util_mean':statistics.mean([g[0] for g in gpu_samples]) if gpu_samples else None,'gpu_temperature_max':max((g[2] for g in gpu_samples),default=None),'cache':cache_state()}
    report['runs'].append(run);print(json.dumps({'run':iteration+1,'ips':run['images_per_second'],'stages':run['stages']},ensure_ascii=False),flush=True)
max_delta=0
for row in rows:
    expected=array('f');expected.frombytes(row['vector']);actual=array('f');actual.frombytes(lib.db.execute('SELECT vector FROM embeddings WHERE file_id=?',(row['id'],)).fetchone()[0]);max_delta=max(max_delta,max(abs(a-b) for a,b in zip(expected,actual,strict=True)))
report['max_vector_delta_vs_original']=max_delta
report['original_vector_hash_after']=original_hash();assert report['original_vector_hash_after']==protected
lib.close();report['closed_database_bytes']=(data/'index.sqlite3').stat().st_size;source.close();monitor_stop.set()
if gpu:gpu.terminate();gpu.wait(timeout=10)
report['median_ips']=statistics.median(r['images_per_second'] for r in report['runs'])
(out/(args.label+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'median_ips':report['median_ips'],'max_vector_delta':max_delta},indent=2))
