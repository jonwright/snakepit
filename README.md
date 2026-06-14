# Snakepit 🐍

Multi-Python Apptainer containers for testing scientific Python C extensions across Python 2.7 through 3.14.

## Quick Start

### Build Containers

```bash
apptainer build --fakeroot ubuntu20.04.sif ubuntu20.04.def
apptainer build --fakeroot ubuntu24.04.sif ubuntu24.04.def
```

No `sudo` required—uses Apptainer's fakeroot capability.

### Test a Python Version

```bash
./test_in_container.sh python3.14 ubuntu24.04.sif
./test_in_container.sh python2.7 ubuntu20.04.sif
```

### Use Containers

```bash
# Interactive shell for Python 2.7, 3.8 (Ubuntu 20.04)
apptainer exec --bind $(pwd):/workspace ubuntu20.04.sif bash

# Interactive shell for Python 3.9-3.14 (Ubuntu 24.04)
apptainer exec --bind $(pwd):/workspace ubuntu24.04.sif bash
```

## Supported Python Versions

| Container | Python Versions |
|-----------|----------------|
| `ubuntu20.04.sif` | 2.7, 3.8 |
| `ubuntu24.04.sif` | 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 |

## Features

- ✅ All Python versions include development headers
- ✅ Git and build-essential pre-installed
- ✅ Supports NumPy f2py for building Fortran/C extensions
- ✅ **No sudo required**—built with fakeroot
- ✅ Automatic file ownership (non-root by default)
- ✅ Virtual environments persist on mounted volumes
- ✅ Perfect for HPC environments

## Example Workflow

```bash
# Run container with workspace mount
apptainer exec --bind $(pwd):/workspace ubuntu24.04.sif bash

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
./test_in_container.sh python3.11 ubuntu24.04.sif

# Test Python 2.7
./test_in_container.sh python2.7 ubuntu20.04.sif
```

All tests validate NumPy, h5py, numba, and C extension compilation/execution.

## License

TBD

## Contributing

Contributions welcome! Please ensure all tests pass before submitting PRs.
