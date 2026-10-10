"""Exact float32 index / float64 query dot product, without an AI dependency.

The Windows helper mirrors CPython 3.14's compensated sum and uses no CRT.
Other platforms and source checkouts without the helper retain Python sum.
"""
from array import array
import ctypes
import math
from pathlib import Path
import sys

_native = None
if sys.platform == 'win32' and sys.version_info[:2] == (3, 14):
    path = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'native' / 'exact-search.dll'
    if path.is_file():
        try:
            _library = ctypes.CDLL(str(path))
            _native = _library.exact_dot
            _native.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_double), ctypes.c_uint]
            _native.restype = ctypes.c_double
        except (OSError, AttributeError):
            # An incomplete installation must retain correct Python ranking.
            _native = None


class ExactDot:
    def __init__(self, query):
        self.query = tuple(float(v) for v in query)
        if not self.query or not all(math.isfinite(v) for v in self.query):
            raise ValueError('検索ベクトルが不正です。AI環境の診断を実行してください')
        self.buffer = (ctypes.c_double * len(self.query))(*self.query)

    def __call__(self, blob):
        if len(blob) != len(self.query) * 4:
            return None
        if _native:
            score = _native(blob, self.buffer, len(self.query))
        else:
            values = array('f'); values.frombytes(blob)
            score = sum(a * b for a, b in zip(values, self.query))
        return score if math.isfinite(score) else None


def implementation():
    return 'native-cpython-3.14-compensated' if _native else 'python-sum'
