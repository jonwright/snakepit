# Snakepit: Multi-Python Version Testing Environment

## Overview

Snakepit provides Docker/Apptainer images for testing scientific Python extensions across multiple Python versions. The images contain system-installed Python interpreters with development headers, allowing users to create virtual environments on mounted filesystems and test C extensions with numpy.

## Image Specifications

### Image 1: snakepit:u20 (Ubuntu 20.04)

**Base:** Ubuntu 20.04 LTS

**Python Versions:**
- Python 2.7 (from system repositories)
- Python 3.8 (from system repositories - default for Ubuntu 20.04)

**System Packages:**
- git
- build-essential (gcc, g++, make, etc.)
- python2.7, python2.7-dev
- python3.8, python3.8-dev, python3.8-venv
- pip for each Python version

### Image 2: snakepit:u24 (Ubuntu 24.04)

**Base:** Ubuntu 24.04 LTS

**Python Versions:**
- Python 3.9.25 (via uv)
- Python 3.10.20 (via uv)
- Python 3.11.15 (via uv)
- Python 3.12.3 (from system repositories - default for Ubuntu 24.04)
- Python 3.13.14 (via uv)
- Python 3.14.6 (via uv)

**System Packages:**
- git
- build-essential (gcc, g++, make, etc.)
- uv (Python version manager)
- python3.12, python3.12-dev, python3.12-venv
- pip for all Python versions

## Usage Workflow

1. **Mount local filesystem** into the container
2. **Create virtual environment** using Python from the container:
   ```bash
   docker run -v $(pwd):/workspace snakepit:u24 python3.11 -m venv /workspace/venv_py311
   ```
3. **Install numpy/scipy** into the venv:
   ```bash
   source venv_py311/bin/activate
   pip install numpy scipy
   ```
4. **Build C extensions** using numpy.f2py or other tools

## Extension Build Process

The recommended workflow for testing C extensions:

1. Write a C function (no Python.h headers needed for f2py)
2. Create an f2py signature file (.pyf)
3. Generate wrapper code: `python -m numpy.f2py module.pyf`
4. Compile manually:
   ```bash
   gcc -shared -fPIC \
       -I$(python -c "import sysconfig; print(sysconfig.get_path('include'))") \
       -I$(python -c "import numpy; print(numpy.get_include())") \
       -I$(python -c "import numpy, os; print(os.path.join(os.path.dirname(numpy.__file__), 'f2py', 'src'))") \
       modulemodule.c module.c \
       $(python -c "import numpy, os; print(os.path.join(os.path.dirname(numpy.__file__), 'f2py', 'src', 'fortranobject.c'))") \
       -o module.so
   ```

This approach avoids dependency on Python version-specific build systems (distutils/setuptools/meson).

## Test Case

A reference test extension is provided that:
- Takes two numpy arrays as input
- Sums them element-wise
- Returns the result array

This validates that:
- The Python interpreter works
- Virtual environments can be created
- numpy installs correctly
- C extensions compile and link properly
- The extension can be imported and used

## Design Rationale

### Why Two Images?

- **Ubuntu 20.04**: Last LTS with Python 2.7 in official repositories; also includes Python 3.8
- **Ubuntu 24.04**: Modern LTS with comprehensive Python 3.x coverage (3.9-3.14) using `uv`

Combined, these images provide Python versions: **2.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14**

### Why System Python?

- Consistent, reproducible environments
- No need to build Python from source
- Faster image builds
- Standard installation paths

### Why Virtual Environments Outside the Container?

- Allows testing with different numpy versions without rebuilding images
- Enables sharing venvs across container runs
- Separates image build from dependency installation
- User controls numpy/scipy versions

### Why Manual Compilation?

- numpy's f2py build system changed significantly in Python 3.12+
- Manual compilation works consistently across all Python versions
- Avoids dependencies on meson, ninja, distutils, or setuptools
- More control over the build process

## Future Enhancements

Potential additions:
- Legacy Python versions (3.6, 3.7) if needed (must be built from source - EOL)
- Apptainer .def files alongside Dockerfiles
- CI/CD for automated image builds
- Multi-architecture support (amd64, arm64)
- Pre-built wheels for common test scenarios

## Notes

- **Python 3.6 and 3.7** have reached end-of-life and are no longer available in Ubuntu repositories or deadsnakes PPA. If needed, they must be built from source.
- **Python 2.7** is the primary use case for the Ubuntu 20.04 image, as it's the last Ubuntu LTS to include it in official repositories.
