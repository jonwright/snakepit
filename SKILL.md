# Snakepit Container Usage Guide for AI Agents

## Overview

Snakepit provides pre-built Apptainer containers with multiple Python versions for testing scientific Python C extensions. The containers bundle Python interpreters (2.7 through 3.15), build tools (gcc, make), and development headers so you can compile and test C extensions without installing anything on the host.

This guide teaches you (an LLM/AI agent) how to use these containers effectively.

## Prerequisites

- **Apptainer** (formerly Singularity) must be installed on the host.
- The `.sif` container files must be built (see below) or provided.
- Container builds require `--fakeroot` (no sudo needed, but user namespaces must be enabled).

## Available Containers

| Image File | Base OS | Python Versions | Where They Come From |
|------------|---------|-----------------|---------------------|
| `ubuntu20.04.sif` | Ubuntu 20.04 | 2.7, 3.8 | Ubuntu repos |
| `debian10.sif` | Debian 10 (Buster) | 3.6 | Official `python:3.6.15-buster` Docker image |
| `ubuntu24.04.sif` | Ubuntu 24.04 | 3.7, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.14t | deadsnakes PPA + uv (free-threading) |
| `ubuntu26.04.sif` | Ubuntu 26.04 | 3.15, 3.15t | deadsnakes PPA + uv (free-threading) |
| `manylinux2014.sif` | CentOS 7 (glibc 2.17) | 3.9, 3.10, 3.11, 3.12, 3.13, 3.14 | manylinux2014 image (GCC 10, auditwheel, uv) |

## Building Containers

All containers build with fakeroot (no sudo):

```bash
apptainer build --fakeroot ubuntu20.04.sif ubuntu20.04.def
apptainer build --fakeroot debian10.sif debian10.def
apptainer build --fakeroot ubuntu24.04.sif ubuntu24.04.def
apptainer build --fakeroot ubuntu26.04.sif ubuntu26.04.def
apptainer build --fakeroot manylinux2014.sif manylinux2014.def
```

**Note**: First build downloads the base Docker image (1-2 GB). Subsequent builds are fast.

## Core Operations

### 1. Run a Single Command Inside a Container

```bash
apptainer exec ubuntu24.04.sif python3.11 -c "print('hello')"
```

### 2. Get an Interactive Shell

```bash
apptainer exec --bind $(pwd):/workspace ubuntu24.04.sif bash
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

## Testing Your Changes

### Test a Specific Python Version

The `test_in_container.sh` script automates the full test cycle (venv -> pip install -> build C ext -> run tests):

```bash
./test_in_container.sh python3.11 ubuntu24.04.sif
```

### Test All Versions

```bash
python3 test_images.py
```

This iterates through all Python versions across all containers.

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
apptainer build --fakeroot manylinux2014.sif manylinux2014.def
```

The manylinux image is rebuilt regularly by the pypa/manylinux project and includes CPython 3.9+.

### Free-Threading (no-GIL) Build in Ubuntu Containers

Add to the `.def` file's uv section:
```bash
uv python install cpython-3.X.0+freethreaded-linux-x86_64-gnu || \
    echo "Free-threading not available"
```

Then symlink it:
```bash
FTPYTHON=$(uv python find cpython-3.X.*+freethreaded* 2>/dev/null || true)
if [ -n "$FTPYTHON" ]; then
    FTBIN=$(dirname "$FTPYTHON")
    ln -s "$FTPYTHON" /usr/local/bin/python3.Xt
fi
```

### Register in `test_images.py`

Add a tuple to the `PYTHON_VERSIONS` list:
```python
("3.X", "ubuntu24.04.sif"),
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
| `test_extension/test_uniform.py` | Python 2.7-3.15 compatible test code |
| `test_extension/requirements.txt` | Version-conditional pip dependencies |
| `test_results.log` | Test output log |

## Common Mistakes to Avoid

1. **Forgetting `--bind`**: Without mounting your workspace, files created inside the container are lost on exit.
2. **Creating venvs outside `/workspace`**: Venvs created in container-internal paths vanish when the container exits.
3. **Using f-strings in test code**: Test code must support Python 2.7, so use `%` formatting or `.format()`.
4. **Using `sudo`**: Container builds use `--fakeroot`; no `sudo` required or available.
5. **Assuming Python X.Y is in a container**: Check `AGENTS.md` or the `.def` file first.
