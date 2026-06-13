# Snakepit 🐍

Multi-Python Docker/Apptainer images for testing scientific Python C extensions across Python 2.7 through 3.14.

## Quick Start

### Build Images

```bash
docker build -f Dockerfile.u20 -t snakepit:u20 .
docker build -f Dockerfile.u24 -t snakepit:u24 .
```

### Run Tests

```bash
python3 test_images.py
```

### Use Images

```bash
# Run container for Python 2.7, 3.6, 3.7, 3.8
docker run --rm -it --user $(id -u):$(id -g) \
  -e HOME=/workspace \
  -v $(pwd):/workspace \
  -w /workspace \
  snakepit:u20 bash

# Run container for Python 3.9-3.14
docker run --rm -it --user $(id -u):$(id -g) \
  -e HOME=/workspace \
  -v $(pwd):/workspace \
  -w /workspace \
  snakepit:u24 bash
```

## Supported Python Versions

| Image | Python Versions |
|-------|----------------|
| `snakepit:u20` | 2.7, 3.6, 3.7, 3.8 |
| `snakepit:u24` | 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 |

## Features

- ✅ All Python versions include development headers
- ✅ Git and build-essential pre-installed
- ✅ Supports NumPy f2py for building Fortran/C extensions
- ✅ Works with Apptainer/Singularity for HPC environments
- ✅ Proper file ownership with `--user` flag
- ✅ Virtual environments persist on mounted volumes

## Example Workflow

```bash
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

The `test_images.py` script validates all Python versions by:
1. Creating a virtual environment
2. Installing NumPy
3. Building a test C extension with f2py
4. Running the extension and validating output

A simple C extension test case is provided in `test_extension/` directory.

## Apptainer Usage

```bash
# Convert Docker images to Apptainer
apptainer build snakepit_u20.sif docker-daemon://snakepit:u20
apptainer build snakepit_u24.sif docker-daemon://snakepit:u24

# Run with Apptainer
apptainer exec --bind $(pwd):/workspace snakepit_u24.sif \
  python3.12 -m venv /workspace/venv_py312
```

## License

TBD

## Contributing

Contributions welcome! Please ensure all tests pass before submitting PRs.
