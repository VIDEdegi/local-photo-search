"""Integration checks against the real model, never the user's photo library."""
import sys, tempfile, time, json, shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'worker'))
from library import Library
from ai import digest

model=root/'data/models/embeddinggemma-2-740m.litertlm'
fixtures=root/'data/fixtures'

def wait(lib):
    deadline=time.monotonic()+120
    while lib.thread and lib.thread.is_alive():
        if time.monotonic()>deadline:raise TimeoutError(lib.status())
        time.sleep(.1)
    assert not lib.progress['last_error'],lib.status()

report={}
with tempfile.TemporaryDirectory(dir=root/'tmp') as temp:
    data=Path(temp)/'index'; photos=Path(temp)/'photos';shutil.copytree(fixtures,photos)
    originals={str(p):digest(p) for p in photos.rglob('*') if p.is_file()}
    lib=Library(data);lib.configure(str(model),'gpu')
    lib.add_folder(str(photos/'objects'));lib.add_folder(str(photos/'landscapes'))
    lib.start();wait(lib)
    assert lib.status()['jobs'].get('done')==4,lib.status()
    assert lib.search(format='png')['total']==1
    assert lib.search(filename='skyline')['total']==1
    assert lib.search(after='2099-01-01')['total']==0
    report['filename_format_date_filters']=True
    queries={'赤いりんごの写真':'still-life.jpg','海辺の風景、砂浜と青い海':'coast.png','森の中の道と木々':'woodland.webp','高いビルが並ぶ街並み':'skyline.jpg'}
    report['japanese_search']={}
    for query,expected in queries.items():
        result=lib.search(text=query)
        ranking=[(r['name'],round(r['score'],4)) for r in result['items']]
        report['japanese_search'][query]=ranking
        assert ranking[0][0]==expected,report
    similar=lib.search(image=str(photos/'objects/still-life.jpg'))
    assert similar['items'][0]['name']=='still-life.jpg'
    report['similar_image_top']=similar['items'][0]['name']
    from PIL import Image
    with Image.open(photos/'landscapes/coast.png') as source:
        source.crop((50,35,590,445)).resize((500,380)).save(Path(temp)/'query.jpg',quality=80)
    variant=lib.search(image=str(Path(temp)/'query.jpg'))
    assert variant['items'][0]['name']=='coast.png',variant
    report['similar_cropped_query_top']=variant['items'][0]['name']
    assert lib.preview(similar['items'][0]['id'])['url'].startswith('data:image/jpeg;base64,')
    indexed=lib.search()['items']; saved={r['id']:r['last_analyzed'] for r in indexed}
    lib.start();wait(lib);assert lib.progress['processed']==0
    report['unchanged_reprocessed']=lib.progress['processed']
    lib.close();lib=Library(data);lib.configure(str(model),'gpu')
    assert lib.search()['total']==4
    assert saved=={r['id']:r['last_analyzed'] for r in lib.search()['items']}
    report['restart_reused']=True
    # Modify one fixture, preserving other embeddings.
    from PIL import Image
    modified=photos/'objects/still-life.jpg'
    with Image.open(modified) as source:source.save(modified,quality=82)
    lib.start();wait(lib);assert lib.progress['processed']==1
    report['changed_reprocessed']=lib.progress['processed']
    (photos/'landscapes/coast.png').unlink();lib.start();wait(lib);assert lib.search()['total']==3
    report['deleted_excluded']=True
    folders=lib.folders();lib.folder_action(folders[0]['id'],'enable',False)
    assert lib.search()['total']==2
    lib.folder_action(folders[0]['id'],'enable',True)
    # Drive loss: unavailable folder must preserve records, but exclude results.
    off=photos/'landscapes';away=photos/'disconnected';off.rename(away)
    lib.start();wait(lib);assert lib.search()['total']==1
    assert lib.status()['total']==3
    away.rename(off);lib.start();wait(lib);assert lib.search()['total']==3
    report['disconnect_reconnect_preserved']=True
    lib.start();lib.pause();wait(lib)
    lib.start();wait(lib);assert lib.search()['total']==3
    report['pause_resume']=True
    lib.close()
    report['original_hashes_before_test']=originals
(root/'data/worker-test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
