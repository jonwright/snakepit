# Snakepit Container Usage Guide for AI Agents

## Overview

Snakepit provides pre-built Apptainer containers with multiple Python versions for testing scientific Python C extensions. The containers bundle Python interpreters (2.7 through 3.16), build tools (gcc, make), and development headers so you can compile and test C extensions without installing anything on the host.

This guide teaches you (an LLM/AI agent) how to use these containers effectively.

## Prerequisites

- **Apptainer** (formerly Singularity) must be installed on the host.
- The `.sif` container files must be built (see below) or provided.
- Container builds require `--fakeroot` (no sudo needed, but user namespaces must be enabled).

## Available Containers

| Image File | Base OS | Python Versions | Where They Come From |
|------------|---------|-----------------|---------------------|
| `snakepit-legacy.sif` | Ubuntu 18.04 (Bionic) | 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9 | native apt (2.7/3.6/3.7) + uv (3.8, PyPy 3.9) + pypy.org tarball (PyPy 2.7) |
| `snakepit-manylinux2014.sif` | CentOS 7 (glibc 2.17) | 3.9, 3.10, 3.11 (tested) | manylinux2014 image (GCC 10). Also ships 3.12/3.13 (which have numpy/h5py wheels) but those aren't tested, and 3.14+/3.14t/3.15/3.15t with no wheels -- see note below |
| `snakepit-manylinux_2_28.sif` | AlmaLinux 8 (glibc 2.28) | 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, PyPy 3.11 (tested) | pypa manylinux_2_28 image (quay.io/pypa/manylinux_2_28_x86_64). No 3.16/3.16t yet |
| `snakepit-modern.sif` | Ubuntu 24.04 | 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, 3.16 (alpha), 3.16t, PyPy 3.11 | deadsnakes PPA (3.9-3.11, 3.13-3.16) + native apt (3.12) + uv (3.14t, 3.15t, 3.16t, PyPy 3.11) |
| `snakepit-p9.sif` | Ubuntu 24.04 + conda-forge (micromamba) | 3.8, 3.11 (numpy 1), 3.12, 3.13, 3.14, 3.15 (numpy 2), 3.14t (free-threading) | one conda-forge env per Python, exposed as `python3.X`. Built and tested natively on POWER9 (ppc64le) -- see `build_p9.sh`, not QEMU |

**Why manylinux2014 stops at 3.11 for real testing**: numpy no longer
publishes `manylinux2014`-tagged wheels for cp314+ (its own wheel baseline
moved to `manylinux_2_28`). The image still carries 3.12/3.13, and numpy
2.2.6 does have manylinux2014 wheels for cp312/cp313, but those two are not
in the test matrix; 3.14 and 3.14t/3.15/3.15t have no wheels at all.
`snakepit-manylinux_2_28.sif` (glibc 2.28) is where numpy >= 2.3, h5py >= 3.15
and cibuildwheel >= 3 wheels land -- the current wheel floor -- while
`snakepit-modern.sif`'s newest glibc is what actually tests 3.12+ and the
pre-release/free-threading builds.

**Why 3.9/3.10/3.11 are in both containers**: this is intentional, not
duplication left over from the consolidation. The original six-container
design tested these three versions against both a modern glibc (Ubuntu
24.04) and an old glibc (CentOS 7/manylinux2014) baseline, and that
dual-glibc coverage is preserved here.

## Building Containers

All containers build with fakeroot (no sudo):

```bash
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-manylinux_2_28.sif snakepit-manylinux_2_28.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

**Note**: First build downloads the base Docker image (1-2 GB). Subsequent builds are fast.

**POWER9 image**: `snakepit-p9.sif` is not built with `apptainer build` here.
Build and test it natively on a POWER9 node with one command from the
checkout: `sbatch build_p9.sh` (see AGENTS.md "Cross-Architecture Containers").

## Core Operations

### 1. Run a Single Command Inside a Container

```bash
apptainer exec snakepit-manylinux2014.sif python3.11 -c "print('hello')"
```

### 2. Get an Interactive Shell

```bash
apptainer exec --bind $(pwd):/workspace snakepit-manylinux2014.sif bash
```

Use `--bind` to mount the current directory into the container (your files appear at `/workspace`).

### 3. Create a Virtual Environment

Inside the container shell:
```bash
python3.11 -m venv /workspace/venv_py311
source /workspace/venv_py311/bin/activate
pip install numpy
```

**Important**: Create venvs on the mounted volume (`/workspace`) so they persist after the container exits.

**Preinstalled packages**: each image bundles numpy/numba/h5py wheels in each
interpreter's system site-packages (see `/opt/snakepit/packages.txt` and the
manifests in `SUMMARY.md`). Use `--system-site-packages` to pick them up; a
plain venv ignores them. Apptainer mounts `$HOME`, so set `PYTHONNOUSERSITE=1`
(else the host's `~/.local/lib/pythonX.Y` shadow them) and give `uv venv
--python` an absolute interpreter path (else uv may pick a Python from the
host's `~/.local/share/uv`):

```bash
apptainer exec snakepit-modern.sif bash -c \
  'python3.12 -m venv --system-site-packages v && PYTHONNOUSERSITE=1 v/bin/python -c "import numpy"'
```

### 4. Build a C Extension with f2py

```bash
python -m numpy.f2py -c -m mymodule mymodule.f
```

### 5. Python 2.7 Special Case

Python 2.7 uses `virtualenv` instead of `venv`:
```bash
python2.7 -m virtualenv /workspace/venv_py27
source /workspace/venv_py27/bin/activate
```

### 5. PyPy (2.7, 3.9, 3.11)

PyPy does not have the `venv` module. Use `virtualenv` for PyPy 2.7,
`uv venv` for PyPy 3.9/3.11:

```bash
# PyPy 2.7
pypy -m ensurepip
pypy -m pip install virtualenv
pypy -m virtualenv /workspace/venv_pypy27
source /workspace/venv_pypy27/bin/activate

# PyPy 3.9 or 3.11 (uv-managed; uv is pre-installed in the container)
uv venv --python pypy3.9 /workspace/venv_pypy39
source /workspace/venv_pypy39/bin/activate
```

Dev headers are at PyPy-specific include paths. Use `sysconfig`:
```bash
pypy3.9 -c "import sysconfig; print(sysconfig.get_path('include'))"
```

The PyPy shared library for cpyext (`libpypy3.X-c.so`) lives alongside the
PyPy binary. Symbol names are prefixed with `PyPy_` (e.g., `PyPyLong_Type`
instead of `PyLong_Type`).

Extensions may need the `.pypy-73.so` suffix (check `sysconfig.get_config_var('SO')`).

## Testing Your Changes

### Test a Specific Python Version

The `test_in_container.sh` script automates the full test cycle (venv -> pip install -> build C ext -> run tests):

```bash
./test_in_container.sh python3.11 snakepit-manylinux2014.sif
```

### Test All Versions

```bash
python3 test_images.py
```

This iterates through all Python versions across all containers. Entries whose
image is a different architecture than the current host, or whose `.sif` is
not built, are skipped (not failed).

### Testing against numpy 1 (ESRF)

The ESRF `module load jupyter-slurm` environment is numpy 1 even in its newest
release, so it is the recommended numpy 1 test. From the snakepit checkout, on
any host with Slurm access (no `module load` needed; the script uses the
environment's path directly):

```bash
sbatch test_numpy_abi.sh            # default numpy 1 = jupyter-slurm latest
srun -p nice bash test_numpy_abi.sh
# optional first arg: a different numpy 1 Python
```

`test_numpy_abi.sh` runs from the snakepit checkout and needs
`snakepit-modern.sif`. It uses the jupyter-slurm Python as the numpy 1 side
and `snakepit-modern.sif` python3.12 (numpy 2.5.4) as the numpy 2 side:
- A: `test_extension/run_tests.sh` against the numpy 1 env's own packages -> OK
- B: build with numpy 2, import under numpy 1 -> OK
- C: build with numpy 1, import under numpy 2 -> ImportError (one-way ABI)

It exits 1 on any other outcome. See the README "numpy 1 vs numpy 2" section.

## Adding a New Python Version

Different containers use different package sources. Follow the pattern for your container type:

### Ubuntu Containers (apt-based)

Add to the `.def` file's apt-get install block:
```bash
python3.X python3.X-dev python3.X-venv \
```

### manylinux2014 Container

Python versions are pre-installed in the manylinux2014 Docker image at `/opt/python/`. If a new Python is available upstream, rebuild the container to pull the latest image:
```bash
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
```

The manylinux image is rebuilt regularly by the pypa/manylinux project and includes CPython 3.9+.

### Free-Threading (no-GIL) Build in Ubuntu Containers

Add to the `.def` file's uv section:
```bash
uv python install cpython-3.X.0+freethreaded-linux-x86_64-gnu || \
    echo "Free-threading not available"
```

`uv python install` already creates a working `python3.Xt` shim in
`/root/.local/bin/` on its own -- no manual symlinking needed as long as
`/root/.local/bin` is on `PATH` (set in `%environment`). A `uv python find
cpython-3.X.*+freethreaded*` + manual `ln -s` step is sometimes added
defensively, but the glob doesn't expand the way you'd expect from inside a
`%post` script (bash passes the literal unexpanded pattern to `uv` when
nothing local matches it), so treat any manual symlink step as a no-op
fallback, not the thing actually making the binary available.

### Register in `test_images.py`

Add a tuple to the `PYTHON_VERSIONS` list:
```python
("3.X", "snakepit-modern.sif"),
```

### Rebuild the Container

```bash
apptainer build --fakeroot <container>.sif <container>.def
```

### Run Full Test Suite

```bash
python3 test_images.py
```

## File Ownership

Apptainer runs as a non-root user by default. Files created inside the container on mounted volumes automatically have the correct host ownership. No `chown` needed.

## ASCII Encoding Requirement

All source files in this repo must use only 7-bit ASCII. No Unicode, emoji, or non-ASCII characters. See `AGENTS.md` for details.

## Reference: Test Infrastructure

| File | Purpose |
|------|---------|
| `*.def` | Apptainer container definitions (one per base OS) |
| `test_in_container.sh` | Run a single Python version's test suite |
| `test_images.py` | Automated runner for all Python versions |
| `test_extension/` | Example C extension + test code |
| `test_extension/run_tests.sh` | In-container test orchestrator |
| `test_extension/build_extension.sh` | f2py C extension build script |
| `test_extension/test_uniform.py` | Python 2.7-3.16 compatible test code |
| `test_extension/requirements.txt` | Version-conditional pip dependencies |
| `test_results.log` | Test output log |

## Common Mistakes to Avoid

1. **Forgetting `--bind`**: Without mounting your workspace, files created inside the container are lost on exit.
2. **Creating venvs outside `/workspace`**: Venvs created in container-internal paths vanish when the container exits.
3. **Using f-strings in test code**: Test code must support Python 2.7, so use `%` formatting or `.format()`.
4. **Using `sudo`**: Container builds use `--fakeroot`; no `sudo` required or available.
5. **Assuming Python X.Y is in a container**: Check `AGENTS.md` or the `.def` file first.
