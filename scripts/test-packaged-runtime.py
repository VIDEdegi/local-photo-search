"""Pinning, official package bytes, real frozen process, TLS; no user index."""
import hashlib,json,os,subprocess,tempfile,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'data/release-tests/rc-audit'
worker=root/'dist-worker/media-search-worker';internal=worker/'_internal'
package=out/'python.3.14.8.nupkg'
assert hashlib.sha256(package.read_bytes()).hexdigest()=='ce85f674d9a63029f709cbff7a3da1c6bc5bfcfaefdd9999f98fa0290470c454'
matched=[]
with zipfile.ZipFile(package) as archive:
    official={Path(n).name.lower():n for n in archive.namelist() if n.startswith('tools/') and n.lower().endswith(('.dll','.pyd'))}
    for file in internal.iterdir():
        if file.name.lower() in official:
            assert file.read_bytes()==archive.read(official[file.name.lower()]),file.name
            matched.append(file.name)
assert {'python314.dll','libssl-3.dll','libcrypto-3.dll','sqlite3.dll'}.issubset(matched)
assert not list(internal.glob('api-ms-win-*.dll'))
assert not any((internal/n).exists() for n in ('ucrtbase.dll','MSVCP140.dll','VCRUNTIME140.dll','VCRUNTIME140_1.dll'))
assert not (internal/'litert_lm/vendors/intel_openvino/dispatch/LiteRtDispatch.dll').exists()
env=dict(os.environ,PATH=str(Path(os.environ['WINDIR'])/'System32'))
for name in ('PYTHONHOME','PYTHONPATH'):env.pop(name,None)
with tempfile.TemporaryDirectory(prefix='packed-runtime-',dir=root/'tmp') as data:
    messages=[{'version':1,'id':1,'method':'environment','params':{}},{'version':1,'id':2,'method':'shutdown','params':{}}]
    process=subprocess.run([str(worker/'media-search-worker.exe'),'--data',data],input=''.join(json.dumps(v)+'\n' for v in messages),capture_output=True,text=True,encoding='utf-8',env=env,timeout=45,check=True)
    replies=[json.loads(line) for line in process.stdout.splitlines()]
    result=replies[0]['result'];assert result['python_bundled']
    assert result['python_version']=='3.14.8'
    assert result['openssl_version'].startswith('OpenSSL 3.5.9 ')
    assert result['search_implementation']=='native-cpython-3.14-compensated'
    assert replies[-1]['result']=={'ok':True}
# Read official tiny metadata over HTTPS from this actual build runtime.
import ssl,urllib.request
assert ssl.OPENSSL_VERSION.startswith('OpenSSL 3.5.9 ')
with urllib.request.urlopen('https://www.python.org/robots.txt',timeout=30) as response:
    assert response.status==200 and response.read(4096)
report={'matched_official_cpython_files':matched,'frozen_environment':result,'minimal_path':True,'graceful_exit':True,'https_certificate_verified':True,'native_dependency_sbom_complete':False}
(out/'packaged-runtime.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='frozen_environment'},indent=2))
