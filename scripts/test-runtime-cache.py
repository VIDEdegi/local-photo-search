import tempfile,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'worker'))
from runtime_cache import RuntimeCache
with tempfile.TemporaryDirectory(dir=root/'tmp') as temp:
    cache=RuntimeCache(Path(temp));a=cache.root/('a'*64);a.mkdir()
    old=a/'old.xnnpack_cache';old.write_bytes(b'x'*10)
    unknown=a/'personal.txt';unknown.write_text('preserve')
    cache.prune(limit=5);assert not old.exists() and unknown.exists()
    new=a/'new_mldrift_weight_cache.bin';new.write_bytes(b'x'*10)
    cache.prune(limit=0,keep=a);assert new.exists()
    cache.clear();assert not new.exists() and unknown.read_text()=='preserve'
print('Generated cache eviction, active exclusion and unknown file preservation: passed')
