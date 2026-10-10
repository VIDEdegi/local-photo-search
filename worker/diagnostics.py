"""Read-only environment checks and a sacrificial native runtime probe."""
import ctypes
import importlib.metadata
import json
import os
import platform
import shutil
import ssl
import subprocess
import sys
from pathlib import Path


def environment(data, model):
    from exact_search import implementation
    version = sys.getwindowsversion() if os.name == 'nt' else None
    supported = bool(version and version.build >= 19045 and platform.machine().upper() in ('AMD64', 'X86_64'))
    packages = {}
    for name in ('litert-lm-api', 'Pillow'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            # PyInstaller includes Pillow's executable module but may omit its dist-info.
            if name == 'Pillow':
                try:
                    import PIL
                    packages[name] = PIL.__version__
                except ImportError:
                    packages[name] = None
            else:
                packages[name] = None
    model = Path(model)
    return {'os': platform.platform(), 'architecture': platform.machine(), 'os_supported': supported,
            'free_bytes': shutil.disk_usage(data).free, 'recommended_free': 2 * 1024**3,
            'runtime': packages, 'python_bundled': bool(getattr(sys, 'frozen', False)),
            'python_version': platform.python_version(), 'openssl_version': ssl.OPENSSL_VERSION,
            'search_implementation': implementation(),
            'model_exists': model.is_file(), 'model_bytes': model.stat().st_size if model.is_file() else 0,
            'gpu_note': '実測済み: Windows 11 / RTX 2070。別GPUは実行診断で確認してください。Windows 10 22H2 x64は対象条件ですが実機未検証です。',
            'cpu_note': 'CPUは4スレッド。GPUが使用できない場合に明示選択できます。性能はPCごとに異なります。'}


def probe(model, backend, data):
    arguments = [sys.executable]
    if not getattr(sys, 'frozen', False):
        arguments.append(str(Path(__file__).with_name('main.py')))
    arguments += ['--probe', '--data', str(data), '--model', str(model), '--backend', backend]
    try:
        result = subprocess.run(arguments, capture_output=True, timeout=90,
                                creationflags=0x08000000 if os.name == 'nt' else 0)
        if result.returncode:
            return {'ok': False, 'backend': backend, 'message': 'AIランタイムを実行できません。GPUドライバーを更新するか、CPUを選択して再診断してください。既存の検索データは保持されています。'}
        report = json.loads(result.stdout.decode('utf-8').strip().splitlines()[-1])
        return {'ok': True, 'backend': backend, **report, 'message': 'このPCで文章と画像のAI実行に成功しました。'}
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return {'ok': False, 'backend': backend, 'message': 'AI診断が完了しませんでした。同梱Worker・モデル・GPUドライバーを確認してください。CPUでも再診断できます。'}


def idle_seconds():
    if os.name != 'nt':
        return 0
    class LastInput(ctypes.Structure):
        _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
    value = LastInput()
    value.cbSize = ctypes.sizeof(value)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(value)):
        return 0
    return ((ctypes.windll.kernel32.GetTickCount() - value.dwTime) & 0xffffffff) / 1000
