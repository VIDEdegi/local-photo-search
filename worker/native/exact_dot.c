/* Compensated summation adapted from CPython 3.14.3, Python/bltinmodule.c.
 * Copyright Python Software Foundation; PSF-2.0, see licenses/python/CPython.
 * Compile /fp:strict: no reassociation, FMA, or float32 accumulation.
 * No CRT or OS imports; x64 baseline instruction set. */
int _fltused = 0; /* MSVC floating-point marker; no CRT initialization required. */
__declspec(dllexport) double exact_dot(const float *values, const double *query, unsigned int n) {
    double hi = 0.0, lo = 0.0;
    for (unsigned int i = 0; i < n; ++i) {
        double x = (double)values[i] * query[i];
        double t = hi + x;
        double ah = hi < 0.0 ? -hi : hi;
        double ax = x < 0.0 ? -x : x;
        if (ah >= ax) lo += (hi - t) + x;
        else lo += (x - t) + hi;
        hi = t;
    }
    /* Search rejects non-finite inputs. Preserve CPython's signed-zero rule. */
    return lo != 0.0 ? hi + lo : hi;
}
