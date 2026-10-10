"""Make an isolated source snapshot, preserving the original Git history.

Never uploads or deletes anything. Run after committing the intended changes.
"""
import json,re,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'data/public-source'
assert not out.exists(),'Use an unused destination; never overwrite a publication checkout'
paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
authors=subprocess.check_output(['git','log','--all','--format=%ae'],cwd=root).decode().splitlines()
private_emails={a.encode() for a in authors if '@' in a and 'users.noreply.github.com' not in a}
copied=[]
for name in filter(None,paths):
    path=Path(name)
    assert path.parts[0] not in {'data','tools','target','dist','dist-worker','node_modules','.venv','.git'}
    assert path.suffix.lower() not in {'.exe','.dll','.litertlm','.sqlite3','.db','.key','.pfx','.pem'}
    src=root/path;dst=out/path;dst.parent.mkdir(parents=True,exist_ok=True)
    content=src.read_bytes()
    assert not re.search(rb'gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',content),name
    if path.parts[0]=='docs' and path.suffix in {'.md','.json','.txt'}:
        text=content.decode('utf-8-sig')
        for prefix in ['E:\\EmbeddingGemmaMediaSearch','E:/EmbeddingGemmaMediaSearch','C:\\projects\\embeddinggemma-media-search']:
            text=text.replace(prefix,'PROJECT_ROOT')
        if path.suffix=='.md' and path.name not in {'USER_GUIDE.md','SETUP.md','RELEASE_NOTES_V1.md','RELEASE_PROCESS.md','PUBLICATION_RESULTS.md'}:
            text='> 開発時の記録です。現在の公開方針はLICENSE_SCOPE.mdとRELEASE_PROCESS.mdを優先します。\n\n'+text
        content=text.encode('utf-8')
    assert not any(email in content for email in private_emails),name
    dst.write_bytes(content);copied.append(name)
report={'files':len(copied),'original_history_exported':False,'personal_author_email_exported':False,'private_signing_material_exported':False,'models_database_photos_exported':False}
(root/'data/release-tests/publication/export.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
