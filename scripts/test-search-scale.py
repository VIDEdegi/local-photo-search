"""Synthetic SQLite search, not real photo indexing or precision evaluation."""
import json,sys,tempfile,time
from array import array
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'worker'))
from library import Library
report={}
with tempfile.TemporaryDirectory(dir=root/'tmp') as temporary:
    lib=Library(Path(temporary)/'index')
    try:
        with lib.db:
            lib.db.execute("INSERT INTO folders(id,path,status) VALUES(1,?,'ready')",(str(Path(temporary)/'synthetic-photos'),))
            lib.db.execute("INSERT INTO models VALUES('synthetic','not-a-model',768,'test','l2','test','test','test')")
        class Engine:
            def text(self,_):return [1.0]+[0.0]*767
            def close(self):pass
        lib.engine=Engine();lib.model_id='synthetic';lib.ensure_engine=lambda:None;lib.maintain_runtime_cache=lambda:None
        vector=array('f',[0.5,0.8660254]+[0.0]*766).tobytes()
        for count in (10000,100000):
            existing=lib.db.execute('SELECT COUNT(*) FROM files').fetchone()[0]
            t=time.monotonic()
            with lib.db:
                lib.db.executemany('INSERT INTO files(id,path,name,size,mtime_ns,identity,format) VALUES(?,?,?,?,?,?,?)',((i,str(Path(temporary)/f'synthetic-{i}.jpg'),f'synthetic-{i}.jpg',1,i*1000000000,str(i),'jpg') for i in range(existing+1,count+1)))
                lib.db.executemany("INSERT INTO folder_files VALUES(1,?,'test')",((i,) for i in range(existing+1,count+1)))
                lib.db.execute("UPDATE embeddings SET vector=?",(vector,))
                lib.db.executemany("INSERT INTO embeddings VALUES(?,'synthetic',?)",((i,vector) for i in range(existing+1,count+1)))
                lib.db.execute("UPDATE embeddings SET vector=? WHERE file_id=?",(array('f',[1.0]+[0.0]*767).tobytes(),count))
            lib.invalidate_search()
            start=time.monotonic();result=lib.search(text='合成検索');elapsed=time.monotonic()-start
            assert result['items'][0]['id']==count
            assert result['total']==count and len(result['items'])==60
            start=time.monotonic();second=lib.search(text='合成検索',offset=60);page=time.monotonic()-start
            assert len(second['items'])==60 and not ({r['id'] for r in result['items']}&{r['id'] for r in second['items']})
            report[str(count)]={'semantic_seconds':round(elapsed,3),'second_page_seconds':round(page,3),'database_bytes':lib.status()['database_bytes'],'dimensions':768,'synthetic':True}
            print(json.dumps({str(count):report[str(count)]}),flush=True)
        lib.folder_action(1,'enable',False);assert lib.search(text='合成検索')['total']==0
        lib.folder_action(1,'enable',True);assert lib.search(text='合成検索')['items'][0]['id']==100000
        assert lib.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    finally:lib.close()
(root/'data/release-tests/search-scale.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
