"""Windows executable lifecycle: single instance and child cleanup on hard exit."""
import ctypes,subprocess,time,os,sqlite3,json
from ctypes import wintypes
from pathlib import Path
root=Path(__file__).resolve().parents[1]
exe=Path(os.environ.get('MEDIA_SEARCH_TEST_EXE',str(root/'target/release/embeddinggemma-media-search.exe')))
data=root/'data/lifecycle-test';env=dict(os.environ,MEDIA_SEARCH_DATA=str(data))
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
class Process(ctypes.Structure):
    _fields_=[('dwSize',wintypes.DWORD),('cntUsage',wintypes.DWORD),('pid',wintypes.DWORD),('heap',ctypes.c_size_t),('module',wintypes.DWORD),('threads',wintypes.DWORD),('parent',wintypes.DWORD),('priority',wintypes.LONG),('flags',wintypes.DWORD),('name',wintypes.WCHAR*260)]
kernel.CreateToolhelp32Snapshot.argtypes=[wintypes.DWORD,wintypes.DWORD];kernel.CreateToolhelp32Snapshot.restype=wintypes.HANDLE
kernel.Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Process)];kernel.Process32NextW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Process)]
kernel.CloseHandle.argtypes=[wintypes.HANDLE]
def processes():
    handle=kernel.CreateToolhelp32Snapshot(2,0)
    row=Process();row.dwSize=ctypes.sizeof(row);result=[]
    try:
        available=kernel.Process32FirstW(handle,ctypes.byref(row))
        while available:
            result.append({'pid':row.pid,'parent':row.parent,'name':row.name});available=kernel.Process32NextW(handle,ctypes.byref(row))
    finally:kernel.CloseHandle(handle)
    return result

a=subprocess.Popen([str(exe)],env=env)
try:
    deadline=time.monotonic()+30;children=[]
    while time.monotonic()<deadline:
        children=[p for p in processes() if p['parent']==a.pid and p['name']=='media-search-worker.exe']
        if children and (data/'index.sqlite3').exists():break
        if a.poll() is not None:raise RuntimeError(f'App exited {a.returncode}')
        time.sleep(.2)
    assert len(children)==1,children
    time.sleep(2)
    b=subprocess.Popen([str(exe)],env=env);assert b.wait(timeout=20)==0
    assert len([p for p in processes() if p['parent']==a.pid and p['name']=='media-search-worker.exe'])==1
    child_pid=children[0]['pid'];a.kill();a.wait(timeout=10)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline and any(p['pid']==child_pid for p in processes()):time.sleep(.1)
    assert not any(p['pid']==child_pid for p in processes()),'Worker survived app termination'
    with sqlite3.connect(data/'index.sqlite3') as db:assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    # Actual native WM_CLOSE with background disabled follows the safe shutdown path.
    a=subprocess.Popen([str(exe)],env=env)
    deadline=time.monotonic()+30;children=[]
    while time.monotonic()<deadline:
        children=[p for p in processes() if p['parent']==a.pid and p['name']=='media-search-worker.exe']
        if children:break
        time.sleep(.2)
    assert len(children)==1,children
    child_pid=children[0]['pid'];windows=[]
    user=ctypes.WinDLL('user32',use_last_error=True)
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    def collect(window,_):
        pid=wintypes.DWORD();user.GetWindowThreadProcessId(window,ctypes.byref(pid))
        if pid.value==a.pid and user.IsWindowVisible(window):windows.append(window)
        return True
    callback=callback_type(collect)
    deadline=time.monotonic()+30
    while time.monotonic()<deadline and not windows:
        user.EnumWindows(callback,0);time.sleep(.2)
    assert windows,'Main window not found'
    assert user.PostMessageW(windows[0],0x0010,0,0)
    assert a.wait(timeout=30)==0,'Graceful close failed'
    assert not any(p['pid']==child_pid for p in processes()),'Worker survived graceful close'
    with sqlite3.connect(data/'index.sqlite3') as db:assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    report={'exe':str(exe),'single_instance':True,'worker_killed_with_parent':True,'sqlite_after_parent_kill':'ok','native_close_graceful_exit':True,'worker_stopped_after_native_close':True}
    (root/'data/lifecycle-test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
finally:
    if a.poll() is None:a.kill();a.wait(timeout=10)
