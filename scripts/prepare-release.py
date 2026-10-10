"""Package existing signed artifacts locally; never publish or access user data."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
assert '-' not in version,'Only stable versions belong in this release package'
installer=root/'target/release/bundle/nsis'/f'Local Photo Search_{version}_x64-setup.exe'
signature=installer.with_suffix('.exe.sig')
assert installer.is_file() and signature.is_file(),'Build signed artifacts first'
out=root/'data/releases'/f'v{version}-public';out.mkdir(parents=True,exist_ok=True)
for src in [installer,signature,root/'LICENSE',root/'LICENSE_SCOPE.md',root/'THIRD_PARTY_NOTICES.md',root/'docs/RELEASE_NOTES_V1.md',root/'docs/USER_GUIDE.md']:
    shutil.copyfile(src,out/src.name)
shutil.make_archive(str(out/'licenses'),'zip',root/'licenses')
manifest={'version':version,'notes':(root/'docs/RELEASE_NOTES_V1.md').read_text(encoding='utf-8'),'platforms':{'windows-x86_64':{'url':f'https://github.com/VIDEdegi/local-photo-search/releases/download/v{version}/'+installer.name.replace(' ','%20'),'signature':signature.read_text(encoding='utf-8').strip()}}}
(out/'latest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
hashes=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS')
(out/'SHA256SUMS').write_text(hashes,encoding='utf-8')
print(installer.name,installer.stat().st_size,hashlib.sha256(installer.read_bytes()).hexdigest())
