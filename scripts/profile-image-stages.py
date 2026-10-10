"""Read-only warm I/O/decode/preprocess diagnostics; never flush global OS caches."""
import io,json,sqlite3,statistics,sys,time
from pathlib import Path
from PIL import Image,ImageOps
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'worker'))
from ai import prepare_image
out=root/'data/performance-audit'
db=sqlite3.connect((root/'data/index.sqlite3').as_uri()+'?mode=ro',uri=True)
rows=db.execute('SELECT f.path FROM files f JOIN embeddings e ON e.file_id=f.id ORDER BY f.id').fetchall()
paths=[Path(rows[round(i*(len(rows)-1)/23)][0]) for i in range(24)]
stages={name:[] for name in ['read','decode','exif_rgb','resize_ai','encode_ai','resize_thumbnail','encode_thumbnail']}
bytes_read=0;max_pixels=0
for path in paths:
    t=time.perf_counter();raw=path.read_bytes();stages['read'].append(time.perf_counter()-t);bytes_read+=len(raw)
    t=time.perf_counter();source=Image.open(io.BytesIO(raw));source.load();stages['decode'].append(time.perf_counter()-t)
    max_pixels=max(max_pixels,source.width*source.height)
    t=time.perf_counter();rgb=ImageOps.exif_transpose(source).convert('RGB');stages['exif_rgb'].append(time.perf_counter()-t)
    for edge,suffix in [(1024,'ai'),(320,'thumbnail')]:
        t=time.perf_counter();image=rgb.copy();image.thumbnail((edge,edge));stages['resize_'+suffix].append(time.perf_counter()-t)
        t=time.perf_counter();buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=95);stages['encode_'+suffix].append(time.perf_counter()-t)
        assert buffer.getvalue()==prepare_image(path,edge)
        image.close()
    rgb.close();source.close()
report={'count':len(paths),'bytes_read':bytes_read,'max_pixels':max_pixels,'stages':{name:{'mean_ms':statistics.mean(values)*1000,'p95_ms':sorted(values)[-2]*1000,'total_seconds':sum(values)} for name,values in stages.items()},'warm_read_mib_per_second':bytes_read/2**20/sum(stages['read']),'prepared_bytes_match':True,'scope':'Warm OS cache; does not establish cold USB disk throughput.'}
(out/'image-stages.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));db.close()
