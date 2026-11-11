# Snakepit

Multi-Python Apptainer containers for testing scientific Python C extensions across Python 2.7 through 3.16, including free-threading (3.14t, 3.15t, 3.16t) and PyPy (2.7, 3.9, 3.11).

Four containers, each sourcing every interpreter as a binary from a package
manager (apt, deadsnakes PPA, uv/python-build-standalone, or pypy.org) --
never compiled from source by this repo:

- **`snakepit-legacy.sif`** (Ubuntu 18.04): 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9
- **`snakepit-manylinux2014.sif`** (CentOS 7, glibc 2.17): 3.9, 3.10, 3.11
- **`snakepit-manylinux_2_28.sif`** (AlmaLinux 8, glibc 2.28): 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, PyPy 3.11
- **`snakepit-modern.sif`** (Ubuntu 24.04): 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, 3.16 (alpha), 3.16t, PyPy 3.11

Each container targets a different glibc baseline. `snakepit-manylinux2014.sif`
(glibc 2.17) is the oldest baseline -- for wheels still tagged manylinux2014
(e.g. bslz4_to_sparse, c2ImageD11 x86_64) -- but only numpy <= 2.2.6 and
h5py <= 3.14.0 publish wheels for it, so its real package testing stops at
3.9-3.11. `snakepit-manylinux_2_28.sif` (glibc 2.28) is the current wheel
floor of the scientific stack (numpy >= 2.3, h5py >= 3.15, cibuildwheel >= 3
by default) and is the right place to test downstream wheels that are no
longer manylinux2014-only. `snakepit-modern.sif` (Ubuntu 24.04) is the newest
glibc plus the pre-release interpreters (3.16, free-threading 3.16t) and
PyPy 3.11.

3.9/3.10/3.11 are deliberately tested in **both** `snakepit-manylinux2014.sif`
(old glibc 2.17) and `snakepit-modern.sif` (modern glibc) -- preserving the
original six-container design's dual-glibc coverage for those three
versions. `snakepit-manylinux2014.sif` also ships interpreters for 3.12 and
3.13 (pre-built in the upstream pypa image; numpy 2.2.6 still has
manylinux2014 wheels for cp312/cp313, so numpy and h5py 3.14.0 are present
there), but those two are not in the test matrix. 3.14 and 3.14t/3.15/3.15t
have no manylinux2014 wheels at all. `snakepit-modern.sif`'s newer glibc/GCC
is what actually gets those versions real package-based testing -- see
`specification.md` for details.

Downstream wheels still tagged manylinux2014 (for example bslz4_to_sparse and
c2ImageD11 x86_64, which auditwheel flagged glibc-2.17 compatible) should be
tested on **both** manylinux images -- `snakepit-manylinux2014.sif` for the
old-glibc claim, `snakepit-manylinux_2_28.sif` for the modern wheel floor.

## Quick Start

### Build Containers

```bash
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-manylinux_2_28.sif snakepit-manylinux_2_28.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

No `sudo` required - uses Apptainer's fakeroot capability.

**Build host note**: the images were built with `apptainer build --fakeroot` on an
Ubuntu 20.04 host (glibc 2.31) with no `/etc/subuid` entry. On an Ubuntu 24.04
host lacking a subuid entry, the manylinux2014 build fails: Apptainer injects
the host's `faked` (which needs GLIBC_2.33/2.34) into the CentOS 7 (glibc
2.17) image. The manylinux_2_28 image (glibc 2.28) likely hits the same
`faked` GLIBC_2.33/2.34 problem on an Ubuntu 24.04 host without subuid (not
tested); it builds fine on the Ubuntu 20.04 host. Fix: add subuid/subgid
entries for the user, or build on an older host. Point `APPTAINER_TMPDIR`/
`APPTAINER_CACHEDIR` at local disk for large builds.

### Test a Python Version

```bash
./test_in_container.sh python3.14 snakepit-modern.sif
./test_in_container.sh python2.7 snakepit-legacy.sif
./test_in_container.sh pypy3.9 snakepit-legacy.sif
```

### Use Containers

```bash
# Interactive shell for Python 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9 (Ubuntu 18.04)
apptainer exec --bind $(pwd):/workspace snakepit-legacy.sif bash

# Interactive shell for Python 3.9, 3.10, 3.11 (manylinux2014, CentOS 7, old glibc)
apptainer exec --bind $(pwd):/workspace snakepit-manylinux2014.sif bash

# Interactive shell for Python 3.9-3.15, 3.14t, 3.15t, PyPy 3.11 (AlmaLinux 8, glibc 2.28)
apptainer exec --bind $(pwd):/workspace snakepit-manylinux_2_28.sif bash

# Interactive shell for Python 3.9-3.16, 3.14t, 3.15t, 3.16t, PyPy 3.11 (Ubuntu 24.04, modern glibc)
apptainer exec --bind $(pwd):/workspace snakepit-modern.sif bash
```

### Use Preinstalled Scientific Packages

Every image preinstalls numpy/numba/h5py wheels into each interpreter's
system site-packages at build time (see `/opt/snakepit/packages.txt` in the
image, and the four manifest tables in `SUMMARY.md`). To use them, make your
venv with `--system-site-packages`; a plain venv ignores them. Because
Apptainer mounts `$HOME`, also set `PYTHONNOUSERSITE=1` (so `~/.local` does
not shadow the image's packages) and pass an absolute interpreter path to
`uv venv --python` (so uv does not pick a Python from the host's
`~/.local/share/uv`):

```bash
apptainer exec snakepit-modern.sif bash -c \
  'python3.12 -m venv --system-site-packages v && PYTHONNOUSERSITE=1 v/bin/python -c "import numpy"'
```

`test_images.py` defaults to testing the preinstalled packages
(`SNAKEPIT_TEST_MODE=fresh` instead pip-installs wheels into an empty venv).

## Supported Python Versions

| Container | Python Versions | Base |
|-----------|----------------|------|
| `snakepit-legacy.sif` | 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9 | Ubuntu 18.04 |
| `snakepit-manylinux2014.sif` | 3.9, 3.10, 3.11 | CentOS 7 (glibc 2.17) |
| `snakepit-manylinux_2_28.sif` | 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, PyPy 3.11 | AlmaLinux 8 (glibc 2.28) |
| `snakepit-modern.sif` | 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, 3.16 (alpha), 3.16t, PyPy 3.11 | Ubuntu 24.04 |

3.9/3.10/3.11 appear in both `snakepit-manylinux2014.sif` and
`snakepit-modern.sif` on purpose (old-glibc leg + modern-glibc leg).

PyPy 2.7 uses `virtualenv`; PyPy 3.9/3.11 use `uv venv` for isolated environments.

## Features

- [OK] All Python versions include development headers
- [OK] Git and build-essential pre-installed
- [OK] Supports NumPy f2py for building Fortran/C extensions
- [OK] **No sudo required** - built with fakeroot
- [OK] Automatic file ownership (non-root by default)
- [OK] Virtual environments persist on mounted volumes
- [OK] Perfect for HPC environments

## Example Workflow

```bash
# Run container with workspace mount
apptainer exec --bind $(pwd):/workspace snakepit-manylinux2014.sif bash

# Inside container
python3.11 -m venv venv_py311
source venv_py311/bin/activate
pip install numpy scipy
python -m numpy.f2py -c -m mymodule mymodule.f
python -c "import mymodule; print(mymodule.myfunc())"
```

## Documentation

See [specification.md](specification.md) for complete documentation including:
- Architecture details
- Usage patterns
- Apptainer/Singularity integration
- Technical implementation notes
- Compatibility information

## Testing

The `test_in_container.sh` script tests a specific Python version by:
1. Creating a virtual environment
2. Installing NumPy and required packages
3. Building a test C extension with f2py
4. Running the extension and validating output
5. Testing h5py and numba functionality

A simple C extension test case is provided in `test_extension/` directory.

### Run Tests

```bash
# Test a specific Python version
./test_in_container.sh python3.11 snakepit-manylinux2014.sif

# Test Python 2.7
./test_in_container.sh python2.7 snakepit-legacy.sif

# Test PyPy 3.9
./test_in_container.sh pypy3.9 snakepit-legacy.sif
```

All tests validate NumPy, h5py, numba, and C extension compilation/execution.

## Cross-Testing *All* Python Versions

To run every supported Python version (2.7 through 3.16, free-threading
builds, and PyPy) across all four containers in one shot:

```bash
python3 test_images.py
```

This reads the `PYTHON_VERSIONS` list in `test_images.py` -- the single
source of truth for which (version, container) pairs are tested -- builds
nothing itself (build the four `.sif` files first, see Quick Start above),
runs each version's full venv -> pip install -> f2py build -> execute cycle,
and writes a pass/fail summary plus full logs to `test_results.log`. It stops
at the first failure by default so you can debug interactively:

```bash
apptainer shell -e -B $(pwd)/test_workspace:/workspace snakepit-<container>.sif
```

**Version-to-container map** (see `specification.md` for the full rationale):

| Python version(s) | Container |
|---|---|
| 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9 | `snakepit-legacy.sif` |
| 3.9, 3.10, 3.11 (old glibc) | `snakepit-manylinux2014.sif` |
| 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, PyPy 3.11 (current wheel floor) | `snakepit-manylinux_2_28.sif` |
| 3.9, 3.10, 3.11 (modern glibc), 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t, 3.16, 3.16t, PyPy 3.11 | `snakepit-modern.sif` |

To test one version by hand instead of the whole matrix, use
`test_in_container.sh <python_cmd> <container>.sif` as shown above, or run
`test_extension/run_tests.sh` directly inside an `apptainer exec`/`shell`
session (see SKILL.md for the manual step-by-step).

### Deploying on an HPC system

The four `.sif` files are self-contained and portable -- build them once
(anywhere with Apptainer and network access), then copy them to shared
storage on the cluster and reference them by absolute path from job scripts;
no network access or root is needed on the compute nodes:

```bash
# On a build host:
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-manylinux_2_28.sif snakepit-manylinux_2_28.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
scp snakepit-*.sif hpc:/apps/snakepit/

# In a job script on the cluster:
apptainer exec --bind $PWD:/workspace /apps/snakepit/snakepit-modern.sif \
    bash -c "python3.14 -m venv /workspace/venv && ..."
```

**Multi-architecture note**: this repo also has `ubuntu20.04_ppc64le.def` /
`ubuntu24.04_aarch64.def`, narrow QEMU-emulated smoke-test containers (each
just Python 3.11) predating the `snakepit-*` four-container layout above.
Building full `ppc64le`/`aarch64` equivalents of `snakepit-legacy` /
`snakepit-manylinux2014` / `snakepit-manylinux_2_28` / `snakepit-modern`
(same version matrix, same naming pattern, e.g.
`snakepit-modern-aarch64.sif`) is planned but not yet done -- it needs a host
with `qemu-user-static` and binfmt_misc handlers registered (see AGENTS.md),
and hasn't been built or tested anywhere yet.

## License

TBD

## Contributing

Contributions welcome! Please ensure all tests pass before submitting PRs.
