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

### Four-Image Strategy

The project uses four images to handle different Python versions across multiple OS generations:

#### Image 1: `snakepit:u20` (Ubuntu 20.04)
- **Python 2.7** (from Ubuntu 20.04 repos)
- **Python 3.8** (from Ubuntu 20.04 repos)

#### Image 2: `snakepit:deb10` (Debian 10)
- **Python 3.6** (from official python:3.6.15-buster Docker image)

#### Image 3: `snakepit:u24` (Ubuntu 24.04)
- **Python 3.7** (from deadsnakes PPA)
- **Python 3.9** (from deadsnakes PPA)
- **Python 3.10** (from deadsnakes PPA)
- **Python 3.11** (from deadsnakes PPA)
- **Python 3.12** (from deadsnakes PPA)
- **Python 3.13** (from deadsnakes PPA)
- **Python 3.14** (from deadsnakes PPA)
- **Python 3.14t** (free-threading/no-GIL, from uv python-build-standalone)

#### Image 4: `snakepit:u26` (Ubuntu 26.04)
- **Python 3.15** (from deadsnakes PPA -- tracks latest beta/rc/final)
- **Python 3.15t** (free-threading/no-GIL, from uv python-build-standalone, if available)

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
# For Python 2.7, 3.8 (Ubuntu 20.04)
apptainer exec --bind /path/to/your/project:/workspace \
  ubuntu20.04.sif bash

# For Python 3.6 (Debian 10)
apptainer exec --bind /path/to/your/project:/workspace \
  debian10.sif bash

# For Python 3.7, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t (Ubuntu 24.04)
apptainer exec --bind /path/to/your/project:/workspace \
  ubuntu24.04.sif bash

# For Python 3.15 (Ubuntu 26.04)
apptainer exec --bind /path/to/your/project:/workspace \
  ubuntu26.04.sif bash
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
# Build Ubuntu 20.04 container (Python 2.7, 3.8)
apptainer build --fakeroot ubuntu20.04.sif ubuntu20.04.def

# Build Debian 10 container (Python 3.6)
apptainer build --fakeroot debian10.sif debian10.def

# Build Ubuntu 24.04 container (Python 3.7, 3.9-3.14, 3.14t)
apptainer build --fakeroot ubuntu24.04.sif ubuntu24.04.def

# Build Ubuntu 26.04 container (Python 3.15)
apptainer build --fakeroot ubuntu26.04.sif ubuntu26.04.def
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
# Test Python 3.14 in Ubuntu 24.04 container
./test_in_container.sh python3.14 ubuntu24.04.sif

# Test Python 2.7 in Ubuntu 20.04 container
./test_in_container.sh python2.7 ubuntu20.04.sif
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
# Build Ubuntu 20.04 container (Python 2.7, 3.8)
apptainer build --fakeroot ubuntu20.04.sif ubuntu20.04.def

# Build Debian 10 container (Python 3.6)
apptainer build --fakeroot debian10.sif debian10.def

# Build Ubuntu 24.04 container (Python 3.7, 3.9-3.14, 3.14t)
apptainer build --fakeroot ubuntu24.04.sif ubuntu24.04.def

# Build Ubuntu 26.04 container (Python 3.15)
apptainer build --fakeroot ubuntu26.04.sif ubuntu26.04.def
```

The `--fakeroot` flag enables rootless builds without requiring `sudo`, making these containers suitable for HPC environments and non-root deployments.

## Technical Details

### Python Version Sources

- **Python 2.7, 3.8**: Ubuntu 20.04 official repositories
- **Python 3.6**: Official [python:3.6.15-buster](https://hub.docker.com/_/python) Docker image (Debian 10)
- **Python 3.7**: [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)
- **Python 3.9-3.14**: [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)
- **Python 3.15**: [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) (resolute builds for Ubuntu 26.04)

### Why Four Images?

1. **Ubuntu 20.04** holds Python 2.7 (last LTS with official support)
2. **Debian 10** provides Python 3.6 via official Docker image
3. **Ubuntu 24.04** provides newer toolchains for Python 3.7-3.14
4. **Ubuntu 26.04** provides the latest toolchain for Python 3.15+
5. Splitting reduces individual image sizes
6. Allows independent updates for legacy vs. modern Python ecosystems

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

VERSIONS_U20="2.7 3.8"
VERSIONS_DEB10="3.6"
VERSIONS_U24="3.7 3.9 3.10 3.11 3.12 3.13 3.14 3.14t"

# Test on u20 container
for ver in $VERSIONS_U20; do
    echo "Testing Python $ver on ubuntu20.04.sif..."
    apptainer exec --bind $(pwd):/workspace ubuntu20.04.sif bash -c "
        cd /workspace
        python${ver} -m venv venv_py${ver//.}
        source venv_py${ver//.}/bin/activate
        pip install numpy
        python setup.py build_ext --inplace
        python -m pytest
      "
done

# Test on u24 container
for ver in $VERSIONS_U24; do
    echo "Testing Python $ver on ubuntu24.04.sif..."
    apptainer exec --bind $(pwd):/workspace ubuntu24.04.sif bash -c "
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
|-- ubuntu20.04.def        # Apptainer definition (Python 2.7, 3.8)
|-- debian10.def           # Apptainer definition (Python 3.6)
|-- ubuntu24.04.def        # Apptainer definition (Python 3.7, 3.9-3.14, 3.14t)
|-- ubuntu26.04.def        # Apptainer definition (Python 3.15, 3.15t)
|-- ubuntu20.04.sif        # Built container (generated)
|-- ubuntu24.04.sif        # Built container (generated)
|-- ubuntu26.04.sif        # Built container (generated)
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
- Pre-release (beta) tracked via deadsnakes PPA - automatically updates as new betas/RCs/final release
- Installed from `ppa:deadsnakes/ppa` on Ubuntu 26.04
- Feature freeze already in effect; expected stable: 2026-10-01
- Free-threading version (`python3.15t`) installed via uv if available in python-build-standalone

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
