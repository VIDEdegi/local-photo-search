"""Stable release: existing isolated index, installed app, one Japanese query."""
import base64, hashlib, json, os, socket, sqlite3, subprocess, time, urllib.request
from contextlib import closing
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
data = Path(os.environ.get('MEDIA_SEARCH_TEST_DATA', str(root / 'data/release-tests/rc-audit/ui-runtime')))
exe = Path(os.environ.get('MEDIA_SEARCH_TEST_EXE', str(root / 'data/release-tests/installed-qa' / (config.get('mainBinaryName', 'embeddinggemma-media-search') + '.exe'))))
assert data.resolve().is_relative_to((root / 'data/release-tests').resolve()), 'Isolated data only'

def vectors():
    with closing(sqlite3.connect((data / 'index.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        rows = list(db.execute('SELECT file_id,model_id,vector FROM embeddings ORDER BY file_id,model_id'))
        assert len(rows) == 4 and db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        return hashlib.sha256(b''.join(str(i).encode() + m.encode() + v for i, m, v in rows)).hexdigest()

before = vectors()
with socket.socket() as sock, socket.socket() as native_sock:
    sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    native_sock.bind(('127.0.0.1', 0)); native_port = native_sock.getsockname()[1]
endpoint = f'http://127.0.0.1:{port}'
env = dict(os.environ, MEDIA_SEARCH_DATA=str(data))
log = (root / 'data/release-tests/v1-driver.log').open('w', encoding='utf-8')
driver = subprocess.Popen([str(root / 'tools/tauri-driver/bin/tauri-driver.exe'), '--port', str(port),
                           '--native-port', str(native_port),
                           '--native-driver', str(root / 'tools/edgedriver/msedgedriver.exe')],
                          env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)

def request(method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    with urllib.request.urlopen(urllib.request.Request(endpoint + path, data=body, method=method,
                               headers={'Content-Type': 'application/json'}), timeout=90) as response:
        value = json.load(response).get('value')
    if isinstance(value, dict) and value.get('error'): raise RuntimeError(value)
    return value

def wait(action):
    until = time.monotonic() + 90
    while time.monotonic() < until:
        value = action()
        if value: return value
        time.sleep(.25)
    raise TimeoutError('Release smoke condition not satisfied')

base = None
try:
    def ready():
        try: return request('GET', '/status')
        except (OSError, urllib.error.URLError): return False
    wait(ready)
    session = request('POST', '/session', {'capabilities': {'alwaysMatch': {'tauri:options': {'application': str(exe)}}}})['sessionId']
    base = '/session/' + session
    request('POST', base + '/timeouts', {'script': 90000})
    def js(script): return request('POST', base + '/execute/sync', {'script': script, 'args': []})
    def rpc(method):
        value = request('POST', base + '/execute/async', {'script': "const done=arguments[arguments.length-1];window.__TAURI_INTERNALS__.invoke('worker_request',{method:arguments[0],params:{}}).then(result=>done({result})).catch(e=>done({error:String(e)}));", 'args': [method]})
        assert 'error' not in value, value
        return value['result']
    wait(lambda: js("return !!document.querySelector('media-search-app')?.shadowRoot?.querySelector('#query')"))
    status = rpc('status'); assert Path(status['data_path']).resolve() == data.resolve(), status['data_path']
    assert not status['running'] and not status['preferences']['resume_on_launch']
    js("const r=document.querySelector('media-search-app').shadowRoot,q=r.querySelector('#query');q.value='海辺の風景';q.dispatchEvent(new Event('input',{bubbles:true}));r.querySelector('form').requestSubmit();")
    wait(lambda: js("return document.querySelector('media-search-app').shadowRoot.querySelector('.card-name')?.textContent==='coast.png'"))
    js("document.querySelector('media-search-app').shadowRoot.querySelector('release-controls[mode=assistant]').openHelp()")
    help_text = wait(lambda: js("return document.querySelector('media-search-app').shadowRoot.querySelector('release-controls[mode=assistant]').shadowRoot.querySelector('#help')?.textContent"))
    assert f"{config['productName']} {config['version']}" in help_text
    assert js('return document.title') == config['app']['windows'][0]['title']
    preferences = request('POST', base + '/execute/async', {'script': "const done=arguments[arguments.length-1];window.__TAURI_INTERNALS__.invoke('update_preferences',{automatic:false}).then(result=>done({result})).catch(e=>done({error:String(e)}));", 'args': []})
    assert 'error' not in preferences and preferences['result']['automatic'] is False
    js("document.querySelector('media-search-app').shadowRoot.querySelector('release-controls[mode=assistant]').close('#help')")
    (root / 'docs/images/search.png').write_bytes(base64.b64decode(request('GET', base + '/screenshot')))
    report = dict(version=config['version'], product=config['productName'], installed_app=True, webview2=True, packaged_worker=True,
                  window_title=True, update_preferences_saved=True,
                  japanese_search_ui='海辺の風景 -> coast.png', stable_about=True,
                  reindex_called=False, vectors_sha256=before, vectors_unchanged=vectors() == before,
                  clean_windows_test=False)
    assert report['vectors_unchanged']
    report_path = Path(os.environ.get('MEDIA_SEARCH_TEST_REPORT', str(root / f"data/release-tests/{config['productName'].replace(' ', '-')}-{config['version']}-smoke.json")))
    assert report_path.resolve().is_relative_to((root / 'data/release-tests').resolve())
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
finally:
    if base:
        try: request('DELETE', base)
        except Exception: pass
    driver.terminate(); driver.wait(timeout=10); log.close()
