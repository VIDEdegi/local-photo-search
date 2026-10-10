# Exact search helper

`worker/native/exact_dot.c` adapts the compensated summation in
[CPython 3.14.3 Python/bltinmodule.c](https://github.com/python/cpython/blob/v3.14.3/Python/bltinmodule.c).
Copyright Python Software Foundation. The complete PSF license and notices
are included in `licenses/python/CPython/LICENSE.txt`.

Changes: read SQLite float32 vectors and a float64 query directly; return the
dot product over the same left-to-right products; reject non-finite output in
the Python caller. Build with strict floating-point arithmetic, no CRT,
no OS imports, and the baseline Windows x64 instruction set. No AVX requirement.
No model, image preprocessing, stored vector, or database schema changes.
