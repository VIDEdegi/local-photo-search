"""Package existing signed artifacts locally; never publish or access user data."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
config=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
version=config['version']
product=config['productName']
notes=root/'src-tauri'/next(p for p,dest in config['bundle']['resources'].items() if dest=='RELEASE_NOTES.md')
assert '-' not in version,'Only stable versions belong in this release package'
installer=root/'target/release/bundle/nsis'/f'{product}_{version}_x64-setup.exe'
signature=installer.with_suffix('.exe.sig')
asset_name=installer.name.replace(' ','-')
assert installer.is_file() and signature.is_file(),'Build signed artifacts first'
out=root/'data/releases'/f'v{version}-public';out.mkdir(parents=True,exist_ok=True)
for src in [installer,signature,root/'LICENSE',root/'LICENSE_SCOPE.md',root/'THIRD_PARTY_NOTICES.md',notes,root/'docs/USER_GUIDE.md']:
    name=asset_name if src==installer else asset_name+'.sig' if src==signature else src.name
    shutil.copyfile(src,out/name)
shutil.make_archive(str(out/'licenses'),'zip',root/'licenses')
release_base=config['bundle']['homepage'].rstrip('/')
manifest={'version':version,'notes':notes.read_text(encoding='utf-8'),'platforms':{'windows-x86_64':{'url':f'{release_base}/releases/download/v{version}/'+asset_name,'signature':signature.read_text(encoding='utf-8').strip()}}}
(out/'latest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
names={asset_name,asset_name+'.sig','LICENSE','LICENSE_SCOPE.md','THIRD_PARTY_NOTICES.md',notes.name,'USER_GUIDE.md','licenses.zip','latest.json'}
hashes=''.join(hashlib.sha256((out/name).read_bytes()).hexdigest()+'  '+name+'\n' for name in sorted(names))
(out/'SHA256SUMS').write_text(hashes,encoding='utf-8')
print(installer.name,installer.stat().st_size,hashlib.sha256(installer.read_bytes()).hexdigest())
