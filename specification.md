# Snakepit: Multi-Python Docker Images for Scientific Extension Testing

## Overview

Snakepit provides Docker/Apptainer container images for testing scientific Python C extensions across multiple Python versions, with a focus on supporting legacy Python 2.7 and modern Python 3.x versions.

## Project Goals

1. **Support testing C extensions** across a wide range of Python versions
2. **Enable testing with NumPy/SciPy** from PyPI via virtual environments
3. **Work in HPC environments** where Apptainer (formerly Singularity) is common
4. **Maintain proper file ownership** when mounting host filesystems
5. **Include all necessary build tools** (gcc, Python dev headers, etc.)

## Architecture

### Two-Image Strategy

The project uses two base images to handle different Python versions and their dependencies:

#### Image 1: `snakepit:u20` (Ubuntu 20.04)
- **Python 2.7** (from Ubuntu 20.04 repos)
- **Python 3.6** (from Ubuntu 20.04 repos)
- **Python 3.7** (from Ubuntu 20.04 repos)
- **Python 3.8** (from Ubuntu 20.04 repos)

#### Image 2: `snakepit:u24` (Ubuntu 24.04)
- **Python 3.9** (from deadsnakes PPA)
- **Python 3.10** (from deadsnakes PPA)
- **Python 3.11** (from deadsnakes PPA)
- **Python 3.12** (from deadsnakes PPA)
- **Python 3.13** (from deadsnakes PPA)
- **Python 3.14** (from deadsnakes PPA)

### Common Components

Both images include:
- **Git** - for repository operations
- **build-essential** - gcc, make, and other build tools
- **Python development headers** (`python-dev` packages) for all versions
- **Python venv support** for all versions
- **pip** bootstrapped for each Python version

## Usage Workflow

### 1. Run Container with Volume Mount

Mount your local workspace into the container at `/workspace`:

```bash
# For Python 2.7, 3.6, 3.7, 3.8
docker run --rm -it --user $(id -u):$(id -g) \
  -e HOME=/workspace \
  -v /path/to/your/project:/workspace \
  -w /workspace \
  snakepit:u20 bash

# For Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
docker run --rm -it --user $(id -u):$(id -g) \
  -e HOME=/workspace \
  -v /path/to/your/project:/workspace \
  -w /workspace \
  snakepit:u24 bash
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

## File Ownership

**Critical**: Always run containers with `--user $(id -u):$(id -g)` to ensure files created inside the container have the correct ownership on the host filesystem. This is essential for:
- HPC environments where you don't have root access
- Preventing permission issues with mounted volumes
- Compatibility with Apptainer (which runs non-root by default)

## Apptainer/Singularity Usage

Convert Docker images to Apptainer format:

```bash
# Build Apptainer image from Docker
apptainer build snakepit_u20.sif docker-daemon://snakepit:u20
apptainer build snakepit_u24.sif docker-daemon://snakepit:u24

# Run with Apptainer
apptainer exec --bind /path/to/project:/workspace snakepit_u24.sif bash
```

## Testing

The repository includes a comprehensive test suite (`test_images.py`) that validates:

1. **Virtual environment creation** for each Python version
2. **NumPy installation** in the venv
3. **C extension compilation** using f2py
4. **Extension functionality** via a simple array-sum test

### Running Tests

```bash
# Test all Python versions in both images
python3 test_images.py
```

The test creates a simple C extension (`arraysum.c`) that:
- Takes two NumPy arrays as input
- Adds them element-wise
- Returns the result
- Validates the computation

## Build Instructions

### Building Docker Images

```bash
# Build Ubuntu 20.04 image (Python 2.7, 3.6, 3.7, 3.8)
docker build -f Dockerfile.u20 -t snakepit:u20 .

# Build Ubuntu 24.04 image (Python 3.9-3.14)
docker build -f Dockerfile.u24 -t snakepit:u24 .
```

### Building with Apptainer

```bash
# From Dockerfiles
apptainer build snakepit_u20.sif Dockerfile.u20
apptainer build snakepit_u24.sif Dockerfile.u24

# From Docker images (if already built)
apptainer build snakepit_u20.sif docker-daemon://snakepit:u20
apptainer build snakepit_u24.sif docker-daemon://snakepit:u24
```

## Technical Details

### Python Version Sources

- **Python 2.7, 3.6, 3.7, 3.8**: Ubuntu 20.04 official repositories
- **Python 3.9-3.14**: [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)

### Why Two Images?

1. **Ubuntu 20.04** is the last LTS release with Python 2.7 in official repos
2. **Ubuntu 24.04** provides newer toolchains for modern Python versions
3. Splitting reduces individual image size
4. Allows independent updates for legacy vs. modern Python ecosystems

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

VERSIONS_U20="2.7 3.6 3.7 3.8"
VERSIONS_U24="3.9 3.10 3.11 3.12 3.13 3.14"

# Test on u20 image
for ver in $VERSIONS_U20; do
    echo "Testing Python $ver on snakepit:u20..."
    docker run --rm --user $(id -u):$(id -g) -e HOME=/workspace \
      -v $(pwd):/workspace -w /workspace snakepit:u20 bash -c "
        python${ver} -m venv venv_py${ver//.}
        source venv_py${ver//.}/bin/activate
        pip install numpy
        python setup.py build_ext --inplace
        python -m pytest
      "
done

# Test on u24 image
for ver in $VERSIONS_U24; do
    echo "Testing Python $ver on snakepit:u24..."
    docker run --rm --user $(id -u):$(id -g) -e HOME=/workspace \
      -v $(pwd):/workspace -w /workspace snakepit:u24 bash -c "
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
├── Dockerfile.u20          # Ubuntu 20.04 image (Python 2.7, 3.6, 3.7, 3.8)
├── Dockerfile.u24          # Ubuntu 24.04 image (Python 3.9-3.14)
├── specification.md        # This document
├── README.md              # User guide and quick start
├── test_images.py         # Automated test suite
└── test_extension/        # Example C extension for testing
    ├── arraysum.c         # C implementation
    ├── arraysum.pyf       # f2py interface definition
    └── build_extension.sh # Build script
```

## Compatibility Notes

### Python 2.7
- Uses `virtualenv` instead of `venv` (installed via pip)
- NumPy 1.16.x is the last version supporting Python 2.7
- SciPy 1.2.x is the last version supporting Python 2.7

### Python 3.6, 3.7
- End-of-life but still common in legacy HPC environments
- Latest compatible NumPy: 1.19.x (3.6), 1.21.x (3.7)

### Python 3.14
- Bleeding edge, may have limited NumPy/SciPy support
- Included for forward compatibility testing

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
