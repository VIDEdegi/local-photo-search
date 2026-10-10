"""One CPU producer; at most two compressed results queued. No GPU work here."""
import queue, threading

class Prefetch:
    def __init__(self,jobs,prepare,stop):
        self.jobs=jobs;self.prepare=prepare;self.stop=stop
        self.cancel=threading.Event();self.queue=queue.Queue(maxsize=2)
        self.thread=threading.Thread(target=self._produce,name='image-prefetch',daemon=True)
    def _put(self,item):
        while not self.cancel.is_set() and not self.stop.is_set():
            try:self.queue.put(item,timeout=.1);return True
            except queue.Full:pass
        return False
    def _produce(self):
        try:
            for job in self.jobs:
                if self.cancel.is_set() or self.stop.is_set():break
                if not self._put((self.prepare(job),None)):break
        except Exception as exc:
            self._put((None,exc))
        finally:self._put((None,None))
    def __enter__(self):self.thread.start();return self
    def __iter__(self):return self
    def __next__(self):
        while not self.stop.is_set():
            try:
                item,error=self.queue.get(timeout=.1)
                if error:raise error
                if item is None:raise StopIteration
                return item
            except queue.Empty:pass
        raise StopIteration
    def __exit__(self,*args):
        self.cancel.set()
        # Finish the single in-flight decode before DB/configuration may be closed.
        self.thread.join()
        while not self.queue.empty():self.queue.get_nowait()
