"""Disposable cache experiments; original model/index/cache stay untouched."""
import sqlite3,json,sys,time,math,threading,ctypes,argparse
from array import array
from pathlib import Path
from ctypes import wintypes
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'worker'))
from ai import LiteRtBackend,prepare_image
from runtime_cache import RuntimeCache
parser=argparse.ArgumentParser();parser.add_argument('--no-cache-only',action='store_true');args=parser.parse_args()
out=root/'data/performance-audit';label='cache-behavior-nocache' if args.no_cache_only else 'cache-behavior';data=out/label;data.mkdir(exist_ok=False)
cache=RuntimeCache(data);model=root/'data/models/embeddinggemma-2-740m.litertlm'
db=sqlite3.connect((root/'data/index.sqlite3').as_uri()+'?mode=ro',uri=True);rows=db.execute('SELECT f.path,e.vector FROM files f JOIN embeddings e ON e.file_id=f.id ORDER BY f.id').fetchall();rows=[rows[round(i*(len(rows)-1)/11)] for i in range(12)]
prepared=[prepare_image(Path(p)) for p,_ in rows]
original_cache={str(p):p.stat().st_size for p in (root/'data/runtime-cache').rglob('*') if p.is_file()}
kernel=ctypes.WinDLL('kernel32');kernel.GetCurrentProcess.restype=wintypes.HANDLE
class Memory(ctypes.Structure):
 _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ['peak_rss','rss','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private']]
psapi=ctypes.WinDLL('psapi');psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Memory),wintypes.DWORD]
def snapshot():return {str(p.relative_to(cache.root)):p.stat().st_size for p in cache.files()}
report={'count':12,'stages':[]};reference=None
for stage in (['no_cache'] if args.no_cache_only else ['initial_empty','warm_reopen','after_cache_delete','no_cache']):
 if stage=='after_cache_delete':cache.clear()
 before=snapshot();measurements=[];stop=threading.Event()
 def monitor():
  while not stop.wait(.1):
   m=Memory();m.cb=ctypes.sizeof(m)
   if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(m),m.cb):measurements.append((m.rss,m.private))
 thread=threading.Thread(target=monitor,daemon=True);thread.start()
 t=time.perf_counter();engine=LiteRtBackend(model,'gpu',':nocache' if stage=='no_cache' else cache.root);load=time.perf_counter()-t
 after_load=snapshot();t=time.perf_counter();text=engine.text('髱偵＞豬ｷ縺ｮ鬚ｨ譎ｯ');search=time.perf_counter()-t;after_search=snapshot()
 engine.image(prepared[0]);t=time.perf_counter();vectors=[engine.image(image) for image in prepared];elapsed=time.perf_counter()-t;after_images=snapshot()
 if reference is None:reference=vectors
 delta=max(abs(a-b) for expected,actual in zip(reference,vectors) for a,b in zip(expected,actual,strict=True))
 old_delta=0
 for (_,blob),vector in zip(rows,vectors):
  expected=array('f');expected.frombytes(blob);old_delta=max(old_delta,max(abs(a-b) for a,b in zip(expected,vector,strict=True)))
 engine.close();stop.set();thread.join()
 result={'stage':stage,'load_seconds':load,'first_search_seconds':search,'prepared_images_per_second':12/elapsed,'vector_delta_vs_first':delta,'vector_delta_vs_original_float32':old_delta,'cache_before_bytes':sum(before.values()),'cache_after_load_bytes':sum(after_load.values()),'cache_after_search_bytes':sum(after_search.values()),'cache_after_12_images_bytes':sum(after_images.values()),'cache_files_after_images':after_images,'peak_rss_bytes':max(x[0] for x in measurements),'peak_private_bytes':max(x[1] for x in measurements)}
 assert delta<1e-6 and old_delta<1e-6,result
 report['stages'].append(result);(out/(label+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps(result),flush=True)
assert original_cache=={str(p):p.stat().st_size for p in (root/'data/runtime-cache').rglob('*') if p.is_file()}
report['original_cache_unchanged']=True
(out/(label+'.json')).write_text(json.dumps(report,indent=2));db.close()
