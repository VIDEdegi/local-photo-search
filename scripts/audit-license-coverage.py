"""Check the actual Windows Cargo dependency graph against bundled notices.

Run after scripts/env.ps1. This cannot establish the SBOM of native wheels.
"""
import json,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
result=subprocess.run([str(root/'tools/cargo/bin/cargo.exe'),'tree','--manifest-path',str(root/'src-tauri/Cargo.toml'),'--target','x86_64-pc-windows-msvc','--locked','--offline','--prefix','none','--format','{p}'],capture_output=True,text=True,timeout=60,check=True)
packages={(m[1],m[2]) for line in result.stdout.splitlines() if (m:=re.match(r'([^ ]+) v([^ ]+)',line))}
notices=json.loads((root/'licenses/rust-packages.json').read_text(encoding='utf-8'))
indexed={(p['name'],p['version']):p for p in notices}
missing=[list(p) for p in sorted(packages) if p[0]!='embeddinggemma-media-search' and p not in indexed]
missing_files=[list(p) for p in sorted(packages) if p in indexed and not indexed[p].get('included_files')]
missing_paths=[f'{name}-{version}/{file}' for name,version in sorted(packages) if (name,version) in indexed for file in indexed[(name,version)].get('included_files',[]) if not (root/'licenses/rust'/f'{name}-{version}'/file).is_file()]
report={'windows_cargo_tree_packages':len(packages),'missing_inventory':missing,'no_copied_notice_files':missing_files,'missing_notice_paths':missing_paths,'native_wheel_sbom_coverage':False}
out=root/'data/release-tests/rc-audit';out.mkdir(exist_ok=True)
(out/'windows-license-coverage.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
assert not missing,'Windows dependencies absent from the bundled inventory'
assert not missing_files and not missing_paths,'Windows dependency notice files are missing'
