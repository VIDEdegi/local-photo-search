"""Separate installer identity; never replaces the user's installed application."""
import subprocess,re,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'target/release/nsis/x64/installer.nsi'
folder=root/'data/release-tests/installers';folder.mkdir(parents=True,exist_ok=True)
baseline=root/'data/release-tests/baseline-exe';baseline.mkdir(exist_ok=True)
(baseline/'embeddinggemma-media-search.exe').write_bytes((root/'data/release-tests/v0.1.1-original.exe').read_bytes())
base=source.read_text(encoding='utf-8').replace('Local Photo Search','Local Photo Search QA').replace('com.local.embeddinggemma.media-search','com.local.embeddinggemma.media-search.qa')
current=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))['version']
for version in ('0.1.1',current):
    if version=='0.1.1' and (folder/(version+'.exe')).is_file():
        print('Reusing previous isolated baseline installer',flush=True);continue
    text=base.replace(f'!define VERSION "{current}"',f'!define VERSION "{version}"').replace('!define VERSIONWITHBUILD "1.0.0.0"',f'!define VERSIONWITHBUILD "{ "0.1.1.0" if version=="0.1.1" else "1.0.0.0" }"')
    text=text.replace('!define OUTFILE "nsis-output.exe"',f'!define OUTFILE "{folder/version}.exe"')
    if version=='0.1.1':
        text=text.replace(str(root/'target/release/embeddinggemma-media-search.exe'),str(root/'data/release-tests/baseline-exe/embeddinggemma-media-search.exe'))
        text=text.replace(str(root/'dist-worker/media-search-worker'),str(root/'app/worker'))
    if version=='0.1.1':
        text='\n'.join(line for line in text.splitlines() if not (line.strip().startswith('File ') and (matches:=re.findall(r'\"([^\"]+)\"',line)) and str(root/'app/worker') in matches[-1] and not Path(matches[-1]).exists()))
    script=folder/(version+'.nsi');script.write_text(text,encoding='utf-8')
    result=subprocess.run([str(root/'target/.tauri/NSIS/makensis.exe'),'/V2','/NOCD',str(script)],cwd=source.parent,timeout=180)
    if result.returncode:raise SystemExit(result.returncode)
    print(str(folder/(version+'.exe')),flush=True)
