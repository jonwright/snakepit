# Snakepit

Multi-Python Apptainer containers for testing scientific Python C extensions across Python 2.7 through 3.15, including free-threading (3.14t, 3.15t) and PyPy (2.7, 3.9, 3.11).

Three containers, each sourcing every interpreter as a binary from a package
manager (apt, deadsnakes PPA, uv/python-build-standalone, or pypy.org) --
never compiled from source by this repo:

- **`snakepit-legacy.sif`** (Ubuntu 18.04): 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9
- **`snakepit-manylinux2014.sif`** (CentOS 7, glibc 2.17): 3.9, 3.10, 3.11, PyPy 3.11
- **`snakepit-modern.sif`** (Ubuntu 24.04): 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t

`snakepit-manylinux2014.sif` also ships interpreters for 3.12+ (they come pre-built in
the upstream pypa image), but those aren't included in the test matrix: numpy
no longer publishes wheels for that old glibc/GCC baseline above cp311, and
the image's GCC 10.2 can't build numpy from source either. `snakepit-modern.sif`'s
newer glibc/GCC is what actually gets those versions real package-based
testing -- see `specification.md` for details.

## Quick Start

### Build Containers

```bash
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

No `sudo` required - uses Apptainer's fakeroot capability.

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

# Interactive shell for Python 3.9, 3.10, 3.11, PyPy 3.11 (manylinux2014, CentOS 7)
apptainer exec --bind $(pwd):/workspace snakepit-manylinux2014.sif bash

# Interactive shell for Python 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t (Ubuntu 24.04)
apptainer exec --bind $(pwd):/workspace snakepit-modern.sif bash
```

## Supported Python Versions

| Container | Python Versions | Base |
|-----------|----------------|------|
| `snakepit-legacy.sif` | 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9 | Ubuntu 18.04 |
| `snakepit-manylinux2014.sif` | 3.9, 3.10, 3.11, PyPy 3.11 | CentOS 7 (glibc 2.17) |
| `snakepit-modern.sif` | 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t | Ubuntu 24.04 |

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

To run every supported Python version (2.7 through 3.15, free-threading
builds, and PyPy) across all three containers in one shot:

```bash
python3 test_images.py
```

This reads the `PYTHON_VERSIONS` list in `test_images.py` -- the single
source of truth for which (version, container) pairs are tested -- builds
nothing itself (build the three `.sif` files first, see Quick Start above),
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
| 3.9, 3.10, 3.11, PyPy 3.11 | `snakepit-manylinux2014.sif` |
| 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t | `snakepit-modern.sif` |

To test one version by hand instead of the whole matrix, use
`test_in_container.sh <python_cmd> <container>.sif` as shown above, or run
`test_extension/run_tests.sh` directly inside an `apptainer exec`/`shell`
session (see SKILL.md for the manual step-by-step).

### Deploying on an HPC system

The three `.sif` files are self-contained and portable -- build them once
(anywhere with Apptainer and network access), then copy them to shared
storage on the cluster and reference them by absolute path from job scripts;
no network access or root is needed on the compute nodes:

```bash
# On a build host:
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
scp snakepit-*.sif hpc:/apps/snakepit/

# In a job script on the cluster:
apptainer exec --bind $PWD:/workspace /apps/snakepit/snakepit-modern.sif \
    bash -c "python3.14 -m venv /workspace/venv && ..."
```

**Multi-architecture note**: this repo also has `ubuntu20.04_ppc64le.def` /
`ubuntu24.04_aarch64.def`, narrow QEMU-emulated smoke-test containers (each
just Python 3.11) predating the `snakepit-*` three-container layout above.
Building full `ppc64le`/`aarch64` equivalents of `snakepit-legacy` /
`snakepit-manylinux2014` / `snakepit-modern` (same version matrix, same
naming pattern, e.g. `snakepit-modern-aarch64.sif`) is planned but not yet
done -- it needs a host with `qemu-user-static` and binfmt_misc handlers
registered (see AGENTS.md), and hasn't been built or tested anywhere yet.

## License

TBD

## Contributing

Contributions welcome! Please ensure all tests pass before submitting PRs.
