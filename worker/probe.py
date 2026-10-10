"""Run CPU/GPU model checks in separate processes; never uploads inputs."""
import argparse, json, math, time, traceback, tempfile
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--backend', choices=['cpu','gpu'],required=True)
    parser.add_argument('--image')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    report={'backend':args.backend,'model':str(Path(args.model).resolve()),'verified':False}
    start=time.perf_counter()
    try:
        from litert_lm import Backend, Content, EmbeddingEngine, EmbeddingOptions
        backend=Backend.GPU() if args.backend=='gpu' else Backend.CPU(thread_count=4)
        with tempfile.TemporaryDirectory(prefix='litert-probe-',dir=Path(args.output).resolve().parent) as cache, EmbeddingEngine(args.model,backend=backend,vision_backend=backend,cache_dir=cache) as engine:
            report['load_seconds']=time.perf_counter()-start
            embeddings=[]
            for text in ['task: search query | text: 赤いりんごの写真','task: search query | text: 青い海の写真']:
                tick=time.perf_counter()
                vector=engine.compute_embedding(text,options=EmbeddingOptions(normalize=True)).embedding
                embeddings.append(vector)
                report.setdefault('text',[]).append({'dimensions':len(vector),'seconds':time.perf_counter()-tick,'norm':math.sqrt(sum(v*v for v in vector))})
            if args.image:
                tick=time.perf_counter()
                vector=engine.compute_embedding(Content.ImageFile(str(Path(args.image).resolve())),options=EmbeddingOptions(normalize=True)).embedding
                report['image']={'dimensions':len(vector),'seconds':time.perf_counter()-tick,'norm':math.sqrt(sum(v*v for v in vector)),'similarities':[sum(a*b for a,b in zip(q,vector,strict=True)) for q in embeddings]}
            report['verified']=True
    except Exception as exc:
        report['error']=str(exc)
        report['traceback']=traceback.format_exc()
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(key,ctypes.c_size_t) for key in ['peak_rss','rss','peak_paged','paged','peak_nonpaged','nonpaged','pagefile','peak_pagefile','private']]
    memory=Counters();memory.cb=ctypes.sizeof(memory)
    ctypes.windll.kernel32.GetCurrentProcess.restype=wintypes.HANDLE
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(memory),memory.cb):
        report['peak_working_set_bytes']=memory.peak_rss
        report['private_bytes_at_end']=memory.private
    report['total_seconds']=time.perf_counter()-start
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['verified'] else 1

if __name__=='__main__':
    raise SystemExit(main())
