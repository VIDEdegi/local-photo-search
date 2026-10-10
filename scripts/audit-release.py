"""Dependency names/versions only sent to OSV; no user data or tokens."""
import hashlib,json,tomllib,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'data/release-tests';out.mkdir(exist_ok=True)
packages=[]
for item in tomllib.loads((root/'src-tauri/Cargo.lock').read_text(encoding='utf-8'))['package']:
    if item.get('source','').startswith('registry+'):
        packages.append({'package':{'name':item['name'],'ecosystem':'crates.io'},'version':item['version']})
for path,item in json.loads((root/'package-lock.json').read_text(encoding='utf-8'))['packages'].items():
    if path:
        packages.append({'package':{'name':path.rsplit('node_modules/',1)[-1],'ecosystem':'npm'},'version':item['version']})
for line in (root/'worker/requirements-lock.txt').read_text(encoding='utf-8').splitlines():
    if '==' in line:
        name,version=line.split('==');packages.append({'package':{'name':name,'ecosystem':'PyPI'},'version':version})
alerts=[]
for start in range(0,len(packages),100):
    batch=packages[start:start+100]
    request=urllib.request.Request('https://api.osv.dev/v1/querybatch',data=json.dumps({'queries':batch}).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=60) as response:results=json.load(response)['results']
    for package,result in zip(batch,results):
        if result.get('vulns'):alerts.append({**package,'vulnerabilities':result['vulns']})
report={'date':'2026-10-10','database':'https://osv.dev/','packages_checked':len(packages),'alerts':alerts,'native_binary_coverage':False}
(out/'dependency-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
