## uv-installed free-threaded Python (3.14t) cannot create working venvs

### Observed behavior

On the ubuntu24.04 container, `python3.14t` is installed via `uv` at:
`/root/.local/share/uv/python/cpython-3.14.0+freethreaded-linux-x86_64-gnu`

Running `python3.14t -m venv /tmp/v` produces a broken venv:
- `ensurepip` fails during venv creation
- The venv Python can't `import encodings`:
  ```
  Fatal Python error: Failed to import encodings module
  ModuleNotFoundError: No module named 'encodings'
  ```
- `sys.prefix` and `sys.base_prefix` both point at the uv installation path,
  but the venv doesn't resolve that path correctly for stdlib lookup.

### Why this matters for c2py23

c2py23's test suite needs to install the project into an isolated environment
before running tests.  For free-threaded Python, the workaround is to skip
venv entirely and install with `--break-system-packages` directly into the
container's system Python.  This works but is not clean.

### Possible fixes

1. Use a different Python 3.14t install mechanism that supports venvs.
   Python.org tarballs, deadsnakes PPA (when available), or compiling
   from source with the standard layout should produce working venvs.

2. Investigate if `uv venv` (rather than `python3.14t -m venv`) works:
   ```
   uv venv --python python3.14t
   ```

3. Document the venv limitation on FT and accept `--break-system-packages`
   as the workaround in CI scripts.

### Impact

- c2py23 test runners (`run_tests.sh`, `test_all.py`, `test_manylinux.py`)
  cannot use venvs for free-threaded Python testing.
- Any downstream project that tests with c2py23 on FT has the same limitation.
- Not a blocker, but a CI hygiene concern.

### Current status

The `uv venv` workaround (option 2 above) is operational in snakepit's
test runners. `run_tests.sh` detects free-threading builds (`*t`) and uses
`uv venv --python python3.Xt` instead of `python3.Xt -m venv`. This produces
working venvs for 3.14t and 3.15t.

Native `python3.Xt -m venv` support depends on upstream uv/python-build-standalone
fixing the stdlib path resolution for freethreaded installs. Until that is resolved,
the `uv venv` path is the recommended approach.
