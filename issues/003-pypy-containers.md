# PyPy containers for cpyext testing

## Summary

Add PyPy 2.7, 3.9, and 3.11 to the snakepit test matrix for c2py23
cross-platform runtime verification. c2py23 uses `dlopen(NULL)` + `dlsym()`
to resolve `PyPy_*` symbols from `libpypy3.X-c.so`, which requires testing
across multiple PyPy versions with different ABIs.

## Container: ubuntu24.04_pypy.sif

A single `ubuntu:24.04`-based container with three PyPy versions:

| Version | Source | Binary | Library |
|---------|--------|--------|---------|
| PyPy 2.7 | Portable tarball (v7.3.17, final release) | `pypy`, `pypy2.7` | `libpypy2.7-c.so` |
| PyPy 3.9 | Ubuntu apt (`pypy3` package) | `pypy3`, `pypy3.9` | `libpypy3.9-c.so` |
| PyPy 3.11 | uv (`uv python install pypy3.11`) | `pypy3.11` | `libpypy3.11-c.so` |

Each version has pip bootstrapped. PyPy 2.7 includes `virtualenv` (PyPy does
not have the `venv` module from stdlib).

## Build

```bash
apptainer build --fakeroot ubuntu24.04_pypy.sif ubuntu24.04_pypy.def
```

## Test scope

Minimal: numpy import + C extension build via f2py. h5py and numba are
skipped gracefully (no PyPy wheels). c2py23 performs its own dlopen/dlsym
testing separately.

## Test runner changes

- `run_tests.sh`: Added `pypy*` detection branch using `virtualenv` instead
  of `venv`.
- `test_images.py`: Added pypy binary-name handling (version strings starting
  with `pypy` are used as-is instead of `python` + version).

## Known limitations

- numba does not support PyPy (LLVM JIT conflicts with PyPy JIT).
- h5py may not have wheels for all PyPy versions on PyPI.
- PyPy 2.7 is the final release (v7.3.17); no further updates.

## References

- PyPy downloads: https://www.pypy.org/download.html
- c2py23 issue: https://github.com/jonwright/c2py23/issues/72
