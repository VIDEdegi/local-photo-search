"""Fill verified workspace-level notices omitted by six published crates.

Small official license documents only; no model/runtime download. Exact
source commits come from the published crate's .cargo_vcs_info.json.
"""
import json,shutil,tomllib,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/'licenses/rust-packages.json'
entries=json.loads(path.read_text(encoding='utf-8'))
base=next((root/'tools/cargo/registry/src').glob('*'))
names={'alloc-stdlib':'LICENSE','selectors':'MPL-2.0.txt','tauri-plugin':'LICENSE-MIT','webview2-com':'LICENSE','webview2-com-sys':'LICENSE','webview2-com-macros':'LICENSE'}
for entry in entries:
    if entry['name'] not in names:continue
    source=base/(entry['name']+'-'+entry['version'])
    meta=tomllib.loads((source/'Cargo.toml').read_text(encoding='utf-8'))['package']
    vcs=json.loads((source/'.cargo_vcs_info.json').read_text(encoding='utf-8'))
    rev=vcs['git']['sha1'];repo=meta['repository'].rstrip('/')
    name=names[entry['name']]
    url='https://www.mozilla.org/media/MPL/2.0/index.txt' if entry['name']=='selectors' else repo.replace('https://github.com/','https://raw.githubusercontent.com/')+'/'+rev+'/'+name
    directory=root/'licenses/rust'/(entry['name']+'-'+entry['version']);directory.mkdir(exist_ok=True)
    with urllib.request.urlopen(url,timeout=30) as response:content=response.read(1024*1024)
    (directory/name).write_bytes(content)
    (directory/'SOURCE.md').write_text(f"License for {entry['name']} {entry['version']}.\nExact published crate VCS commit: {rev}\nLicense source: {url}\nSource: {repo}/tree/{rev}\n",encoding='utf-8')
    if entry['name']=='selectors':
        assert 'Mozilla Public' in (source/'lib.rs').read_text(encoding='utf-8')
        target=directory/'source';target.mkdir(exist_ok=True)
        for file in source.rglob('*'):
            if file.is_file() and not file.name.startswith('.cargo'):
                dest=target/file.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dest)
        with (directory/'SOURCE.md').open('a',encoding='utf-8') as f:
            f.write('Exact unmodified published crate source accompanies these notices in source/. Cargo and source headers specify MPL-2.0. The repository root has no separate license file; the standard unmodified license is supplied from Mozilla. No source modifications were made. Covered source is available here and at the fixed upstream commit.\n')
    entry['included_files']=[name,'SOURCE.md'];entry['license_source']=url
    print(entry['name'],rev,name,len(content),flush=True)
path.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
