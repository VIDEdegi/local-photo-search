"""One verified import, never overwrites an existing model or removes the source."""
import argparse,hashlib,shutil,os
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def import_model(source,destination):
    source=Path(source).resolve(strict=True);destination=Path(destination).resolve()
    with source.open('rb') as f:
        if f.read(8)!=b'LITERTLM':raise ValueError('LiteRT-LM形式ではありません')
    expected=sha(source)
    if destination.exists():
        if sha(destination)!=expected:raise ValueError('保存先に異なるモデルが存在します。上書きしません')
        return {'path':str(destination),'sha256':expected,'copied':False}
    destination.parent.mkdir(parents=True,exist_ok=True)
    free=shutil.disk_usage(destination.parent).free
    if free<source.stat().st_size+2*1024**3:raise ValueError('モデル容量に加えて2 GiBの空きを確保してください')
    temporary=destination.with_suffix(destination.suffix+'.partial')
    with source.open('rb') as src,temporary.open('xb') as dst:
        shutil.copyfileobj(src,dst,1024*1024);dst.flush();os.fsync(dst.fileno())
    if sha(temporary)!=expected:raise ValueError('SHA-256が一致しません。元ファイルと一時ファイルは保持します')
    # Windows rename does not replace an existing target.
    temporary.rename(destination)
    return {'path':str(destination),'sha256':expected,'copied':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--destination',required=True);args=parser.parse_args()
    print(import_model(args.source,args.destination))
