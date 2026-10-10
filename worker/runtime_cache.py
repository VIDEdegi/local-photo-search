"""Only disposable SDK cache files inside the dedicated app-owned directory."""
from pathlib import Path
import re, shutil
LIMIT=1024**3
RESERVE=768*1024**2

class RuntimeCache:
    def __init__(self,data):
        self.root=(data/'runtime-cache').resolve()
        if (data/'runtime-cache').is_symlink() or (data/'runtime-cache').is_junction():
            raise ValueError('AIキャッシュにリンクは使用できません')
        self.root.mkdir(exist_ok=True)
        self.size=self.usage()
    def files(self):
        # Never traverse links, or delete unknown files placed here by a user.
        for directory in [self.root,*[p for p in self.root.iterdir() if re.fullmatch(r'[0-9a-f]{64}',p.name) and p.is_dir() and not p.is_symlink() and not p.is_junction()]]:
            for file in directory.iterdir():
                if file.is_file() and not file.is_symlink() and file.name.endswith(('.xnnpack_cache','_mldrift_program_cache.bin','_mldrift_weight_cache.bin')):
                    if file.resolve().is_relative_to(self.root):yield file
    def usage(self):
        return sum(p.stat().st_size for p in self.files())
    def prune(self,limit=LIMIT,keep=None):
        entries=[];total=0
        for file in self.files():
            stat=file.stat();total+=stat.st_size
            if keep is None or file.parent!=keep:entries.append((stat.st_mtime,file,stat.st_size))
        for _,file,size in sorted(entries):
            if total<=limit:break
            file.unlink(missing_ok=True);total-=size
        self.size=total
        return total
    def prepare(self,sha):
        path=self.root/sha
        if path.exists() and (path.is_symlink() or path.is_junction()):raise ValueError('AIキャッシュにリンクは使用できません')
        self.prune(limit=LIMIT-RESERVE,keep=path)
        path.mkdir(exist_ok=True)
        if shutil.disk_usage(self.root).free<RESERVE:raise ValueError('AIキャッシュ用に768 MiB以上の空きを確保してください')
        return path
    def clear_generation(self,path):
        # Called only after its engine has closed; never unlink mapped active files.
        if path.parent!=self.root:raise ValueError('不正なAIキャッシュ保存先です')
        for file in list(self.files()):
            if file.parent==path:file.unlink(missing_ok=True)
        self.size=self.usage()
    def clear(self):return self.prune(limit=0)
