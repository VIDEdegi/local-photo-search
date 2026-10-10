import sqlite3, json, time
from pathlib import Path

SCHEMA_VERSION=1
SCHEMA="""
CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE folders(id INTEGER PRIMARY KEY,path TEXT UNIQUE COLLATE NOCASE NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,status TEXT NOT NULL DEFAULT 'new',error TEXT,last_scan REAL);
CREATE TABLE models(id TEXT PRIMARY KEY,sha256 TEXT NOT NULL,dimensions INTEGER NOT NULL,preprocess TEXT NOT NULL,normalization TEXT NOT NULL,query_prefix TEXT NOT NULL,runtime TEXT NOT NULL,backend TEXT NOT NULL);
CREATE TABLE files(id INTEGER PRIMARY KEY,path TEXT UNIQUE COLLATE NOCASE NOT NULL,name TEXT NOT NULL,size INTEGER NOT NULL,mtime_ns INTEGER NOT NULL,identity TEXT NOT NULL,kind TEXT NOT NULL DEFAULT 'image',format TEXT NOT NULL,available INTEGER NOT NULL DEFAULT 1,thumbnail TEXT,last_analyzed REAL,error TEXT);
CREATE TABLE folder_files(folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,seen TEXT NOT NULL,PRIMARY KEY(folder_id,file_id));
CREATE TABLE embeddings(file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,model_id TEXT NOT NULL REFERENCES models(id),vector BLOB NOT NULL,PRIMARY KEY(file_id,model_id));
CREATE TABLE jobs(file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,model_id TEXT NOT NULL REFERENCES models(id),state TEXT NOT NULL DEFAULT 'pending',error TEXT,attempts INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(file_id,model_id));
CREATE INDEX jobs_state ON jobs(model_id,state);
CREATE INDEX folders_file ON folder_files(file_id);
"""

def connect(path:Path):
    db=sqlite3.connect(path,check_same_thread=False,timeout=30)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    version=db.execute('PRAGMA user_version').fetchone()[0]
    if version>SCHEMA_VERSION: raise RuntimeError('このデータは新しいアプリで作られています。新しいバージョンを使用してください。')
    if version<SCHEMA_VERSION:
        if version>0: backup_before_migration(db,path)
        migrations={1:SCHEMA}
        for next_version in range(version+1,SCHEMA_VERSION+1):
            db.executescript('BEGIN IMMEDIATE;'+migrations[next_version]+f'PRAGMA user_version={next_version};COMMIT;')
    db.execute("UPDATE jobs SET state='pending' WHERE state='processing'")
    db.commit()
    return db

def backup_before_migration(db,path:Path):
    destination=path.with_name(path.name+f'.migration-{int(time.time())}.bak')
    with sqlite3.connect(destination) as copy: db.backup(copy)
    return destination
