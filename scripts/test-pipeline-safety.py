"""Functional cancellation, source-change, disk-full and mapped-cache safety checks."""
import hashlib,threading,tempfile,time,sys,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'worker'))
import library
from ai import prepare_image,prepare_index_image
from prefetch import Prefetch
from runtime_cache import RuntimeCache

class FakeEngine:
    def __init__(self,model,backend,cache):self.dimensions=8;self.closed=False;self.cache=cache
    def text(self,text):return [1/8**.5]*8
    def image(self,data):return self.text('')
    def close(self):self.closed=True

class Safety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=root/'tmp');self.path=Path(self.temp.name)
        self.patch=patch.object(library,'LiteRtBackend',FakeEngine);self.patch.start()
        self.model=self.path/'model.litertlm';self.model.write_bytes(b'LITERTLM-test-only')
        self.lib=library.Library(self.path/'index');self.lib.configure(str(self.model),'gpu')
        self.photos=self.path/'photos';self.photos.mkdir()
        for n in range(12):Image.new('RGB',(512,384),(n*20,80,100)).save(self.photos/f'{n}.jpg')
        self.lib.add_folder(str(self.photos))
    def tearDown(self):self.lib.close();self.patch.stop();self.temp.cleanup()
    def wait(self):
        self.lib.thread.join(timeout=10);self.assertFalse(self.lib.thread.is_alive())
        self.assertFalse(any(t.name=='image-prefetch' for t in threading.enumerate()))
    def rows(self):return dict(self.lib.db.execute('SELECT state,COUNT(*) FROM jobs GROUP BY state').fetchall())
    def test_pause_preserves_pending_and_saved_vectors(self):
        entered=threading.Event();release=threading.Event();original=FakeEngine.image
        def blocked(engine,data):entered.set();release.wait(5);return original(engine,data)
        with patch.object(FakeEngine,'image',blocked):
            self.lib.start();self.assertTrue(entered.wait(5));self.lib.pause();release.set();self.wait()
        self.assertEqual(self.rows(),{'done':1,'pending':11})
        saved=self.lib.db.execute('SELECT vector FROM embeddings').fetchone()[0]
        self.lib.start();self.wait();self.assertEqual(self.rows(),{'done':12})
        self.assertEqual(saved,self.lib.db.execute('SELECT vector FROM embeddings ORDER BY file_id').fetchone()[0])
    def test_changed_after_prefetch_cannot_commit_vector(self):
        original=self.lib._prepare_job;changed=[False]
        def prepare(job):
            result=original(job)
            if not changed[0]:
                changed[0]=True;Path(job['path']).write_bytes(b'changed-test-fixture')
            return result
        self.lib._prepare_job=prepare;self.lib.start();self.wait()
        self.assertEqual(self.rows(),{'done':11,'error':1})
        self.assertEqual(self.lib.db.execute('SELECT COUNT(*) FROM embeddings').fetchone()[0],11)
    def test_decode_error_does_not_block_other_files(self):
        (self.photos/'0.jpg').write_bytes(b'invalid-fixture');self.lib.start();self.wait()
        self.assertEqual(self.rows(),{'done':11,'error':1})
    def test_low_disk_leaves_jobs_pending(self):
        from collections import namedtuple
        usage=namedtuple('usage','total used free')(1024**3,1024**3,1)
        with self.lib.ai_lock:self.lib.ensure_engine()
        self.lib._scan(self.lib.folders()[0])
        with patch.object(library.shutil,'disk_usage',return_value=usage):
            self.lib.start();self.wait()
        self.assertEqual(self.rows(),{'pending':12});self.assertEqual(self.lib.progress['phase'],'error')
    def test_live_cap_closes_engine_before_eviction_and_reuses_profile(self):
        with self.lib.ai_lock:self.lib.ensure_engine()
        active=self.lib.runtime_path;old=self.lib.engine;profile=self.lib.model_id
        large=active/'fake_mldrift_weight_cache.bin';large.write_bytes(b'x'*2048)
        unknown=active/'user-note.txt';unknown.write_text('preserve',encoding='utf-8')
        original=self.lib.runtime_cache.clear_generation
        def clear(path):self.assertTrue(old.closed);return original(path)
        with patch.object(library,'LIMIT',1024),patch.object(self.lib.runtime_cache,'clear_generation',clear):
            with self.lib.ai_lock:self.lib.maintain_runtime_cache()
        self.assertFalse(large.exists());self.assertTrue(unknown.exists())
        self.assertEqual(self.lib.engine.cache,':nocache');self.assertEqual(profile,self.lib.model_id)
        self.assertIsNotNone(self.lib.cache_warning)
    def test_inactive_eviction_never_deletes_active_mapped_files(self):
        cache=self.lib.runtime_cache;active=cache.root/('a'*64);inactive=cache.root/('b'*64)
        active.mkdir();inactive.mkdir()
        a=active/'active.xnnpack_cache';a.write_bytes(b'a'*1500)
        b=inactive/'old.xnnpack_cache';b.write_bytes(b'b'*1500)
        self.assertEqual(cache.prune(limit=1024,keep=active),1500)
        self.assertTrue(a.exists());self.assertFalse(b.exists())
    def test_bounded_prefetch_stops_when_consumer_aborts(self):
        count=[]
        with Prefetch(range(100),lambda n:count.append(n) or bytes(100),threading.Event()) as stream:
            next(stream);time.sleep(.15)
            self.assertLessEqual(len(count),4)
        self.assertFalse(stream.thread.is_alive());self.assertTrue(stream.queue.empty())
    def test_preparation_exact_bytes_across_formats_and_exif(self):
        for mode,extension in [('RGB','jpg'),('RGBA','png'),('L','png'),('CMYK','jpg'),('RGB','webp')]:
            path=self.path/(mode+'.'+extension);im=Image.new(mode,(1234,1456));exif=Image.Exif();exif[274]=6
            im.save(path,exif=exif);im.close();before=hashlib.sha256(path.read_bytes()).digest()
            pair=prepare_index_image(path)
            self.assertEqual(pair,(prepare_image(path),prepare_image(path,320)))
            self.assertEqual(before,hashlib.sha256(path.read_bytes()).digest())

if __name__=='__main__':unittest.main(verbosity=2)
