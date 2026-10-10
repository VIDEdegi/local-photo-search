"""Read-only release audit. Compare with the pre-development snapshot; never reset data."""
from contextlib import closing
import hashlib
import json
import sqlite3
import argparse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'data/release-tests'
parser=argparse.ArgumentParser()
parser.add_argument('--snapshot',default='protected-before.json')
parser.add_argument('--report',default='protected-after.json')
parser.add_argument('--capture',action='store_true',help='Create a new baseline; never overwrite an existing one')
args=parser.parse_args()
assert Path(args.snapshot).name==args.snapshot and Path(args.report).name==args.report
snapshot=out/args.snapshot
with closing(sqlite3.connect((root / 'data/index.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
    digest = hashlib.sha256()
    for file_id, model_id, vector in db.execute('SELECT file_id,model_id,vector FROM embeddings ORDER BY file_id,model_id'):
        digest.update(str(file_id).encode() + model_id.encode() + vector)
    current = {
        'vectors_sha256': digest.hexdigest(),
        'files': db.execute('SELECT COUNT(*) FROM files').fetchone()[0],
        'embeddings': db.execute('SELECT COUNT(*) FROM embeddings').fetchone()[0],
        'folders': db.execute('SELECT COUNT(*) FROM folders').fetchone()[0],
        'settings': dict(db.execute('SELECT key,value FROM settings')),
        'integrity': db.execute('PRAGMA integrity_check').fetchone()[0],
        'cache': {str(p.relative_to(root / 'data/runtime-cache')): p.stat().st_size
                  for p in (root / 'data/runtime-cache').rglob('*') if p.is_file()},
    }
if not args.capture:
    before=json.loads(snapshot.read_text(encoding='utf-8'))
    assert current == before, 'Protected user data differs from the selected snapshot'
with (root / 'data/models/embeddinggemma-2-740m.litertlm').open('rb') as model:
    model_sha = hashlib.file_digest(model, 'sha256').hexdigest()
assert model_sha == 'e7a8a2204b91e0f96e92960e84a09a89212e1633dcb7575a9bf3378b4df77f4c'
original_exe = root / 'app/embeddinggemma-media-search.exe'
assert original_exe.read_bytes() == (out / 'v0.1.1-original.exe').read_bytes()
if args.capture:
    with snapshot.open('x',encoding='utf-8') as f:
        json.dump(current,f,ensure_ascii=False,indent=2)
report = dict(current, model_sha256=model_sha, original_installed_exe_unchanged=True, snapshot_matches=True)
(out / args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('settings', 'cache')}, indent=2))
