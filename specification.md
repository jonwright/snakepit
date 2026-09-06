# Snakepit: Multi-Python Apptainer Containers for Scientific Extension Testing

## Overview

Snakepit provides Apptainer container images for testing scientific Python C extensions across multiple Python versions, with a focus on supporting legacy Python 2.7 and modern Python 3.x versions. Built with fakeroot support, no sudo required.

## Project Goals

1. **Support testing C extensions** across a wide range of Python versions
2. **Enable testing with NumPy/SciPy** from PyPI via virtual environments
3. **Work in HPC environments** where Apptainer (formerly Singularity) is common
4. **Maintain proper file ownership** when mounting host filesystems
5. **Include all necessary build tools** (gcc, Python dev headers, etc.)

## Architecture

### Three-Image Strategy

The project uses three images. Each Python version's interpreter is always a
binary from a package manager (apt, deadsnakes PPA, uv/python-build-standalone,
or pypy.org) -- never compiled from source by this repo.

#### Image 1: `snakepit-legacy.sif` (Ubuntu 18.04)
- **Python 2.7** (native bionic main repo)
- **Python 3.6** (native bionic main repo, bionic's default python3)
- **Python 3.7** (native bionic universe repo)
- **Python 3.8** (uv/python-build-standalone prebuilt binary -- no apt/PPA
  source exists for 3.8 anymore; deadsnakes dropped bionic/focal entirely)
- **PyPy 2.7** (pypy.org portable tarball, v7.3.17 final release)
- **PyPy 3.9** (uv prebuilt binary)

#### Image 2: `snakepit-manylinux2014.sif` (CentOS 7)
- **Python 3.9, 3.10, 3.11** (pre-installed in manylinux2014 Docker image at
  `/opt/python/`) -- the only versions actually tested here
- **PyPy 3.11** (also pre-installed, tested here)
- Also ships 3.12-3.15, 3.14t, 3.15t interpreters, but they are NOT in the
  test matrix: numpy no longer publishes manylinux2014 (glibc 2.17) wheels
  for cp312+, and this CentOS 7 image's GCC 10.2 can't build numpy from
  source either (numpy's meson build requires GCC >= 10.3). See "manylinux2014"
  under Compatibility Notes.
- Oldest glibc (2.17) for maximum binary compatibility testing
- GCC 10 toolchain (devtoolset-10) with gfortran for f2py

#### Image 3: `snakepit-modern.sif` (Ubuntu 24.04)
- **Python 3.12** (Ubuntu 24.04's own default python3)
- **Python 3.13, 3.14, 3.15** (deadsnakes PPA -- noble builds; 3.15 tracks
  latest beta/rc/final)
- **Python 3.14t, 3.15t** (free-threading/no-GIL, from uv python-build-standalone)
- Modern glibc (2.39) means numpy/h5py/numba install as real wheels here with
  no source build needed -- this is what manylinux2014 can no longer do for
  these versions.

### Common Components

All images include:
- **Git** - for repository operations
- **build-essential** - gcc, make, and other build tools
- **Python development headers** (`python-dev` packages) for all versions
- **Python venv support** for all versions
- **pip** bootstrapped for each Python version

## Usage Workflow

### 1. Run Container with Volume Mount

Mount your local workspace into the container at `/workspace`:

```bash
# For Python 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9 (Ubuntu 18.04)
apptainer exec --bind /path/to/your/project:/workspace \
  snakepit-legacy.sif bash

# For Python 3.9, 3.10, 3.11, PyPy 3.11 (manylinux2014, CentOS 7)
apptainer exec --bind /path/to/your/project:/workspace \
  snakepit-manylinux2014.sif bash

# For Python 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t (Ubuntu 24.04)
apptainer exec --bind /path/to/your/project:/workspace \
  snakepit-modern.sif bash
```

### 2. Create Virtual Environment

Inside the container, create a virtual environment for the desired Python version:

```bash
# Example for Python 2.7
python2.7 -m virtualenv venv_py27
source venv_py27/bin/activate

# Example for Python 3.11
python3.11 -m venv venv_py311
source venv_py311/bin/activate
```

### 3. Install NumPy/SciPy

```bash
# Inside activated venv
python -m pip install --upgrade pip
python -m pip install numpy scipy
```

### 4. Build C Extension

Use NumPy's f2py or standard distutils/setuptools:

```bash
# Using f2py
python -m numpy.f2py -c -m mymodule mymodule.f

# Or with build script
python setup.py build_ext --inplace
```

## Apptainer Container Usage

### Building Containers

Build the Apptainer SIF images using fakeroot (no sudo required):

```bash
# Build legacy container (Python 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9)
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def

# Build manylinux2014 container (Python 3.9-3.11 tested, PyPy 3.11)
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def

# Build modern container (Python 3.12-3.15, 3.14t, 3.15t)
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

### File Ownership

Apptainer runs as a non-root user by default, which means files created inside the container automatically have the correct ownership on the host filesystem. This is essential for:
- HPC environments where you don't have root access
- Preventing permission issues with mounted volumes
- Cross-platform compatibility

## Testing

The repository includes a comprehensive test suite with **uniform code** that works across all Python versions (2.7-3.15).

### Key Testing Features

1. **Version-conditional requirements.txt** - Uses Python's `python_version` markers to install appropriate packages
2. **No special-casing** - Same test code runs on all Python versions
3. **Single command per version** - One docker run command does everything
4. **Comprehensive validation** - Tests NumPy, h5py, numba, and C extensions

### Requirements File

The `test_extension/requirements.txt` uses conditional dependencies:

```txt
# NumPy
numpy<1.17 ; python_version < "3"
numpy ; python_version >= "3"

# H5Py  
h5py ; python_version >= "2.7"

# Numba and LLVM
llvmlite==0.29.0 ; python_version < "3"
numba==0.45.0 ; python_version < "3"
numba ; python_version >= "3"
```

### Running Tests

You can manually test a specific Python version:

```bash
# Test Python 3.14 in the modern container
./test_in_container.sh python3.14 snakepit-modern.sif

# Test Python 2.7 in the legacy container
./test_in_container.sh python2.7 snakepit-legacy.sif
```

The test validates:
- **Virtual environment creation** for each Python version
- **Package installation** from requirements.txt (with correct versions)
- **C extension compilation** using f2py
- **Extension functionality** via a simple array-sum test
- **h5py** - HDF5 file read/write operations
- **numba** - JIT compilation and execution

The test creates a simple C extension (`arraysum.c`) that:
- Takes two NumPy arrays as input
- Adds them element-wise  
- Returns the result
- Validates the computation

All tests print package versions for verification.

## Build Instructions

### Building Apptainer Containers

```bash
# Build legacy container (Python 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9)
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def

# Build manylinux2014 container (Python 3.9-3.11 tested, PyPy 3.11)
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def

# Build modern container (Python 3.12-3.15, 3.14t, 3.15t)
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

The `--fakeroot` flag enables rootless builds without requiring `sudo`, making these containers suitable for HPC environments and non-root deployments.

## Technical Details

### Python Version Sources

- **Python 2.7, 3.6, 3.7**: native Ubuntu 18.04 (bionic) apt repos (main/universe)
- **Python 3.8**: [uv](https://github.com/astral-sh/uv) / python-build-standalone
  prebuilt binary -- deadsnakes no longer builds for bionic/focal, and no distro
  ships 3.8 natively anymore
- **Python 3.12**: Ubuntu 24.04's own default python3 (native apt)
- **Python 3.13, 3.14, 3.15**: [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) (noble builds)
- **Python 3.14t, 3.15t**: uv / python-build-standalone prebuilt free-threading binaries
- **Python 3.9-3.11 (manylinux2014)**: Pre-installed in [quay.io/pypa/manylinux2014_x86_64](https://quay.io/repository/pypa/manylinux2014_x86_64) Docker image
- **PyPy 2.7**: [pypy.org](https://www.pypy.org/download.html) portable tarball (final release)
- **PyPy 3.9**: uv prebuilt binary
- **PyPy 3.11**: pre-installed in the manylinux2014 image

### Why Three Images?

1. **legacy** (Ubuntu 18.04) is the only base whose own apt repos still carry
   2.7/3.6/3.7 natively; 3.8 and PyPy 3.9 are bolted on via uv since no
   package manager ships them for this distro anymore
2. **manylinux2014** (CentOS 7, glibc 2.17) gives the oldest-glibc binary
   compatibility signal, but only for the CPython versions numpy still
   publishes old-baseline wheels for (3.9-3.11)
3. **modern** (Ubuntu 24.04) covers everything manylinux2014's stale GCC/glibc
   can no longer build or install wheels for (3.12+, free-threading builds)
4. Three images (down from an earlier six) keeps every interpreter binary
   (apt/deadsnakes/uv/pypy.org/manylinux) while avoiding the two
   old-glibc-vs-new-CPython dead ends described above

### Virtual Environment Strategy

Virtual environments are created **outside** the container images for several reasons:

1. **Flexibility**: Users can install any version of NumPy/SciPy
2. **Caching**: venvs persist across container runs via volume mounts
3. **Isolation**: Each Python version gets its own independent environment
4. **Size**: Keeps container images minimal

### Development Headers

All Python versions include development headers (`Python.h`, etc.) which are essential for:
- Compiling C extensions
- NumPy f2py integration
- Cython modules
- SWIG bindings

The build system uses `distutils.sysconfig.get_python_inc()` to correctly locate headers even within virtual environments.

## Example: Testing Across All Versions

```bash
#!/bin/bash
# test_all_versions.sh

VERSIONS_LEGACY="2.7 3.6 3.7 3.8"
VERSIONS_MANYLINUX="3.9 3.10 3.11"
VERSIONS_MODERN="3.12 3.13 3.14 3.14t 3.15 3.15t"

# Test on legacy container
for ver in $VERSIONS_LEGACY; do
    echo "Testing Python $ver on snakepit-legacy.sif..."
    apptainer exec --bind $(pwd):/workspace snakepit-legacy.sif bash -c "
        cd /workspace
        python${ver} -m venv venv_py${ver//.}
        source venv_py${ver//.}/bin/activate
        pip install numpy
        python setup.py build_ext --inplace
        python -m pytest
      "
done

# Test on manylinux2014 container
for ver in $VERSIONS_MANYLINUX; do
    echo "Testing Python $ver on snakepit-manylinux2014.sif..."
    apptainer exec --bind $(pwd):/workspace snakepit-manylinux2014.sif bash -c "
        cd /workspace
        python${ver} -m venv venv_py${ver//.}
        source venv_py${ver//.}/bin/activate
        pip install numpy
        python setup.py build_ext --inplace
        python -m pytest
      "
done

# Test on modern container
for ver in $VERSIONS_MODERN; do
    echo "Testing Python $ver on snakepit-modern.sif..."
    apptainer exec --bind $(pwd):/workspace snakepit-modern.sif bash -c "
        cd /workspace
        python${ver} -m venv venv_py${ver//.}
        source venv_py${ver//.}/bin/activate
        pip install numpy
        python setup.py build_ext --inplace
        python -m pytest
      "
done
```

## Repository Structure

```
snakepit/
|-- snakepit-legacy.def             # Apptainer definition (Python 2.7,3.6,3.7,3.8, PyPy 2.7,3.9)
|-- snakepit-manylinux2014.def      # Apptainer definition (Python 3.9-3.11 tested, CentOS 7)
|-- snakepit-modern.def             # Apptainer definition (Python 3.12-3.15, 3.14t, 3.15t)
|-- snakepit-legacy.sif             # Built container (generated)
|-- snakepit-manylinux2014.sif      # Built container (generated)
|-- snakepit-modern.sif             # Built container (generated)
|-- AGENTS.md              # Agent instructions and quick reference
|-- SKILL.md               # Detailed container usage guide for AI agents
|-- specification.md       # This document
|-- README.md              # User guide and quick start
|-- test_images.py         # Automated test suite
|-- test_in_container.sh   # Test runner script
`-- test_extension/        # Example C extension and tests
    |-- arraysum.c         # C implementation
    |-- arraysum.pyf       # f2py interface definition
    |-- build_extension.sh # Build script (updated for Python 3.14t)
    |-- requirements.txt   # Version-conditional package dependencies
    |-- run_tests.sh       # Unified test runner for all Python versions
    `-- test_uniform.py    # Uniform test code (works on Python 2.7-3.15)
```

## Compatibility Notes

### Python 2.7
- Uses `virtualenv` instead of `venv` (installed via pip)
- NumPy 1.16.x is the last version supporting Python 2.7
- SciPy 1.2.x is the last version supporting Python 2.7

### Python 3.8
- Long-term support version common in production HPC environments
- Latest compatible NumPy and SciPy versions available

### Python 3.14
- Bleeding edge, may have limited NumPy/SciPy support
- Included for forward compatibility testing

### Python 3.14t (Free-Threading)
- CPython build with the Global Interpreter Lock (GIL) disabled
- Installed as `python3.14t` from uv python-build-standalone
- C extensions must be thread-safe - use `sys._is_gil_enabled()` to detect at runtime
- Enables true parallelism for CPU-bound Python threads

### Python 3.15
- Pre-release (beta/RC) tracked via deadsnakes PPA - automatically updates as new betas/RCs/final release
- Installed from `ppa:deadsnakes/ppa` (noble builds) on Ubuntu 24.04 (`snakepit-modern.sif`)
- Feature freeze already in effect; expected stable: 2026-10-01
- Free-threading version (`python3.15t`) installed via uv if available in python-build-standalone

### PyPy 2.7
- Portable tarball from pypy.org (v7.3.17, final PyPy2.7 release, no further updates)
- Sharing a container with native CPython 2.7 (`snakepit-legacy.sif`) exposed a bug in
  `test_extension/build_extension.sh`'s header-path fallback: it picked
  `/usr/include/python2.7` (CPython's headers, present because CPython 2.7
  is installed alongside) before trying PyPy's own `sys.base_prefix`-based
  include path, silently building the extension against the wrong `Python.h`
  and failing at import with `undefined symbol: PyExc_RuntimeError`. Fixed by
  checking `platform.python_implementation() == "PyPy"` first and routing
  PyPy straight to its own include dir; PyPy also now links explicitly
  against `libpypy-c.so` (via an rpath), since PyPy doesn't export its C-API
  symbols to the running process the way CPython does.

### manylinux2014
- CentOS 7 base with glibc 2.17 (oldest compatible glibc)
- All Pythons are pre-installed in `/opt/python/` from the pypa/manylinux Docker image
- GCC 10 toolchain via devtoolset-10 (no newer devtoolset was ever published
  for CentOS 7's SCL repo) with gfortran for f2py
- h5py may not be available for some Python versions due to CentOS 7's old HDF5 (1.8.12)
- **Only 3.9, 3.10, 3.11, and PyPy 3.11 are in the test matrix.** The image
  also ships 3.12, 3.13, 3.14, 3.14t, 3.15, 3.15t interpreters, but numpy no
  longer publishes manylinux2014-tagged wheels for cp312+ (its own wheel
  baseline moved to manylinux_2_28), and building numpy from source fails
  here because numpy's meson build requires GCC >= 10.3 while this image is
  fixed at GCC 10.2.1. Real testing for those versions happens in
  `snakepit-modern.sif` instead, which has a modern enough glibc/GCC for numpy's
  current wheels to install directly.

## Future Enhancements

Potential improvements for future versions:

1. **Pre-built wheels cache** - mount a pip cache to speed up NumPy installs
2. **Multi-arch support** - ARM64 variants for Apple Silicon and ARM servers
3. **Additional tools** - OpenBLAS, MKL, FFTW for performance testing
4. **CI/CD integration** - GitHub Actions workflow for automated testing
5. **Alternative compilers** - Intel, Clang variants for compatibility testing

## License

To be determined by repository owner.

## Contributing

Contributions welcome! Please test across all Python versions before submitting pull requests.

## Acknowledgments

- [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) for modern Python versions
- Ubuntu team for maintaining Python packages in official repos
- NumPy team for f2py and the C API
