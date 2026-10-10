"""Verify installed notice payload, consent and unchanged Worker, in QA only."""
import argparse, hashlib, json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--install-directory', type=Path, required=True)
args = parser.parse_args()
installed = args.install_directory.resolve(strict=True)
assert installed == (root / 'data/release-tests/installed-qa').resolve(), 'QA installation only'
work = root / 'data/release-tests/license-finalization'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

expected = []
for path in sorted((root / 'licenses').rglob('*')):
    if path.is_file():
        target = installed / path.relative_to(root)
        assert target.is_file(), target
        assert sha(path) == sha(target), target
        expected.append(path.relative_to(root).as_posix())
for name, source in [('THIRD_PARTY_NOTICES.md', root / 'THIRD_PARTY_NOTICES.md'),
                     ('USER_GUIDE.md', root / 'docs/USER_GUIDE.md')]:
    assert sha(source) == sha(installed / name), name

before = json.loads((work / 'worker-before.json').read_text(encoding='utf-8'))
worker = root / 'dist-worker/media-search-worker'
current = {p.relative_to(worker).as_posix(): sha(p) for p in sorted(worker.rglob('*')) if p.is_file()}
assert current == before, 'Worker changed during document-only finalization'
for relative, digest in before.items():
    assert sha(installed / 'worker' / relative) == digest, relative
assert not any(Path(p).name.lower().startswith(('vcruntime', 'msvcp', 'api-ms-'))
               or Path(p).name.lower() in ('ucrtbase.dll', 'litertdispatch.dll') for p in current)

sources = json.loads((root / 'licenses/native/LiteRT-third-party/sources.json').read_text())
assert len(sources) == 10
for row in sources:
    path = root / 'licenses/native/LiteRT-third-party' / row['component'] / 'LICENSE'
    assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], path
    assert row['url'].startswith('https://raw.githubusercontent.com/')
eula = json.loads((work / 'webview-eula.json').read_text(encoding='utf-8'))['evergreenHtml']
assert (root / 'licenses/native/WebView2/RUNTIME_EULA.html').read_text(encoding='utf-8') == eula
consent = (root / 'docs/INSTALLER_NOTICE.txt').read_text(encoding='utf-8')
assert (root / 'licenses/native/WebView2/RUNTIME_EULA.txt').read_text(encoding='utf-8') in consent
assert 'SmartScreen' in consent and 'https://aka.ms/privacy' in consent
nsis = (root / 'target/release/nsis/x64/installer.nsi').read_text(encoding='utf-8')
# Tauri creates a UTF-8 BOM copy for NSIS's Unicode license page.
compiled_consent = root / 'target/release/nsis/x64/license_file'
assert compiled_consent.read_bytes().startswith(b'\xef\xbb\xbf')
assert compiled_consent.read_text(encoding='utf-8-sig') == consent
assert str(compiled_consent) in nsis and 'RUNTIME_EULA.html' in nsis
assert 'MUI_PAGE_LICENSE' in nsis

version = json.loads((root / 'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))['version']
report = dict(version=version, qa_only=True, installed_license_files=len(expected),
              installed_notices_equal=True, complete_runtime_eula_equal=True,
              source_license_hashes_verified=len(sources), worker_files_unchanged=len(before),
              excluded_dlls_absent=True, clean_windows_test=False,
              qa_installer_sha256=sha(root / f'data/release-tests/installers/{version}.exe'),
              installer_sha256=sha(root / f'target/release/bundle/nsis/Local Photo Search_{version}_x64-setup.exe'))
(work / 'packaging-results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
