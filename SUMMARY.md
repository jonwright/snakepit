# Snakepit: Simplified Uniform Testing Approach

## What We Built

A Docker/Apptainer-based testing environment for Python C extensions that works **uniformly** across Python 2.7 through 3.16 (including free-threading 3.14t, 3.15t, 3.16t) with **no special-casing**.

## Key Improvements

### 1. Version-Conditional Requirements File [OK]

**Before**: Hard-coded package versions in test script for each Python version

**After**: Single `requirements.txt` with Python version markers:

```txt
numpy<1.17 ; python_version < "3"
numpy ; python_version >= "3"

llvmlite==0.29.0 ; python_version < "3"
numba==0.45.0 ; python_version < "3"
numba ; python_version >= "3"
```

### 2. Uniform Test Code [OK]

**Before**: Version-specific test code with special cases for Python 2.7

**After**: Single `test_uniform.py` that runs unchanged on ALL Python versions
- Uses `from __future__ import print_function`
- No f-strings
- Works identically from Python 2.7 to 3.16

### 3. Simplified Test Runner [OK]

**Before**: Multi-step process with separate commands for:
- Creating venv
- Installing packages  
- Building extension
- Running tests

**After**: Single command does everything:

```bash
docker run --rm --user $(id -u):$(id -g) -e HOME=/workspace \
  -v $(pwd)/test_extension:/workspace -w /workspace \
  snakepit:u24 bash run_tests.sh python3.11
```

### 4. Apptainer Mostly Invisible [OK]

Users can think of it as: "Run this script with this Python version"

The Apptainer container just provides the Python interpreter and build tools.

## Preinstalled Packages

Every image preinstalls numpy/numba/h5py wheels into each interpreter's
system site-packages at build time. The manifest written by
`install_sci_packages.sh` at `/opt/snakepit/packages.txt` (shown below, with
each image's size in MB) says what is actually present -- `-` means no wheel
for that interpreter. Downstream opts in with `venv --system-site-packages`,
or uses a plain venv to ignore the image's packages.

### `snakepit-legacy.sif` (668 MB, 700854272 bytes)

| Interpreter | Python | NumPy | numba | h5py |
|---|---|---|---|---|
| python2.7 | 2.7.17 | 1.16.6 | 0.47.0 | 2.10.0 |
| python3.6 | 3.6.9 | 1.19.5 | 0.53.1 | 3.1.0 |
| python3.7 | 3.7.5 | 1.21.6 | 0.56.4 | 3.8.0 |
| python3.8 | 3.8.20 | 1.24.4 | 0.58.1 | 3.11.0 |
| pypy2.7 | 2.7.18 | - | - | - |
| pypy3.9 | 3.9.19 | 2.0.2 | - | - |

### `snakepit-manylinux2014.sif` (584 MB, 612593664 bytes)

| Interpreter | Python | NumPy | numba | h5py |
|---|---|---|---|---|
| python3.9 | 3.9.25 | 2.0.2 | 0.60.0 | 3.14.0 |
| python3.10 | 3.10.22 | 2.2.6 | 0.67.0 | 3.14.0 |
| python3.11 | 3.11.18 | 2.2.6 | 0.67.0 | 3.14.0 |
| python3.12 | 3.12.16 | 2.2.6 | 0.67.0 | 3.14.0 |
| python3.13 | 3.13.18 | 2.2.6 | 0.67.0 | 3.14.0 |
| python3.14 | 3.14.10 | - | - | - |
| python3.14t | 3.14.10 | - | - | - |
| python3.15 | 3.15.2 | - | - | - |
| python3.15t | 3.15.2 | - | - | - |
| pypy3.11 | 3.11.15 | - | - | - |

### `snakepit-manylinux_2_28.sif` (790 MB, 828825600 bytes)

| Interpreter | Python | NumPy | numba | h5py |
|---|---|---|---|---|
| python3.9 | 3.9.25 | 2.0.2 | 0.60.0 | 3.14.0 |
| python3.10 | 3.10.22 | 2.2.6 | 0.68.1 | 3.16.0 |
| python3.11 | 3.11.18 | 2.4.6 | 0.68.1 | 3.16.0 |
| python3.12 | 3.12.16 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.13 | 3.13.18 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.14 | 3.14.10 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.14t | 3.14.10 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.15 | 3.15.2 | 2.5.4 | 0.68.1 | 3.17.0.dev0 |
| python3.15t | 3.15.2 | 2.5.4 | - | 3.17.0.dev0 |
| pypy3.11 | 3.11.15 | 2.4.6 | - | - |

(no python3.16/3.16t in the pypa base image yet)

### `snakepit-modern.sif` (747 MB, 783081472 bytes)

| Interpreter | Python | NumPy | numba | h5py |
|---|---|---|---|---|
| python3.9 | 3.9.25 | 2.0.2 | 0.60.0 | 3.14.0 |
| python3.10 | 3.10.22 | 2.2.6 | 0.68.1 | 3.16.0 |
| python3.11 | 3.11.18 | 2.4.6 | 0.68.1 | 3.16.0 |
| python3.12 | 3.12.3 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.13 | 3.13.18 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.14 | 3.14.10 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.15 | 3.15.2 | 2.5.4 | 0.68.1 | 3.17.0.dev0 |
| python3.16 | 3.16.0a1 | - | - | - |
| python3.14t | 3.14.10 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.15t | 3.15.2 | 2.5.4 | - | 3.17.0.dev0 |
| python3.16t | 3.16.0a1 | - | - | - |
| pypy3.11 | 3.11.15 | 2.4.6 | - | - |

### `snakepit-p9.sif` (880 MB, 922882048 bytes)

| Interpreter | Python | NumPy | numba | h5py |
|---|---|---|---|---|
| python3.8 | 3.8.20 | 1.24.4 | 0.58.1 | 3.11.0 |
| python3.11 | 3.11.6 | 1.24.4 | 0.57.1 | 3.10.0 |
| python3.12 | 3.12.16 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.13 | 3.13.18 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.14 | 3.14.10 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.15 | 3.15.2 | 2.5.4 | 0.68.1 | 3.16.0 |
| python3.14t | 3.14.10 | 2.5.4 | 0.68.1 | 3.16.0 |

snakepit-p9.sif is built and tested natively on POWER9 (conda-forge binaries).
3.11 is the numpy 1 jupyter-slurm stack (numpy
1.24.4, h5py 3.10.0, numba 0.57.1), 3.8 is also numpy 1; the rest are numpy 2.

Only prebuilt binaries are installed (PyPI wheels, the silx wheelhouse,
scientific-python nightlies, conda-forge); compiling upstream packages is a
smell and is only done to test git heads with no nightly.
3.15/3.15t h5py (3.17.0.dev0) comes from the scientific-python nightly wheel
index until h5py 3.17.0 ships cp315 wheels. 3.16/3.16t and pypy2.7 have no
numpy/numba/h5py wheels and are tested as bare interpreters.

Test matrix (2026-11-11): all 31 entries run against `snakepit-legacy.sif`,
`snakepit-manylinux2014.sif`, `snakepit-manylinux_2_28.sif` and
`snakepit-modern.sif` pass (3.16, 3.16t and pypy2.7 as bare interpreters);
on x86_64 the p9 and aarch64 entries are skipped (different architecture / not
built). On a POWER9 node, `snakepit-p9.sif`'s 7 test entries pass natively
(2026-11-11), and the aarch64 entry is skipped. PyPy 3.11 is tested in
`snakepit-manylinux_2_28.sif` and `snakepit-modern.sif`, no longer in
`snakepit-manylinux2014.sif` (numpy's pp311 wheels need glibc >= 2.28). The
manylinux_2_28 image has no 3.16/3.16t (not in the pypa base image yet).


## What Gets Tested

For each Python version:
1. [OK] Virtual environment creation
2. [OK] Package installation (with correct versions per Python)
3. [OK] C extension compilation with f2py
4. [OK] h5py HDF5 file operations
5. [OK] numba JIT compilation
6. [OK] C extension array operations

## File Structure

```
test_extension/
|-- arraysum.c          # C implementation
|-- arraysum.pyf        # f2py interface
|-- build_extension.sh  # Build script
|-- requirements.txt    # Version-conditional dependencies
|-- run_tests.sh        # Unified test runner
`-- test_uniform.py     # Python 2.7-3.16 compatible test code (incl. free-threading)
```

## Usage Examples

### Test All Versions

```bash
./test_in_container.sh python3.11 snakepit-manylinux2014.sif
```

### Test One Version

```bash
# Python 2.7
./test_in_container.sh python2.7 snakepit-legacy.sif

# Python 3.13
./test_in_container.sh python3.13 snakepit-modern.sif
```

### Manual Interactive Testing

```bash
# Enter container
apptainer exec --bind $(pwd)/test_extension:/workspace snakepit-manylinux2014.sif bash

# Inside container - manually run steps
python3.11 -m venv venv_test
source venv_test/bin/activate
pip install -r requirements.txt
bash build_extension.sh python
python test_uniform.py
```

## Benefits

1. **No Special Cases**: Same code works everywhere
2. **Automatic Version Selection**: requirements.txt handles package versions
3. **Simple**: One command per Python version
4. **Maintainable**: Update requirements.txt, not Python code
5. **Extensible**: Easy to add new Python versions or packages
6. **HPC Ready**: Works with Apptainer/Singularity
7. **Proper Ownership**: Files created with correct user permissions

## Next Steps for Users

1. Replace `arraysum.c` with your own C extension
2. Update `requirements.txt` with your dependencies
3. Modify `test_uniform.py` for your tests
4. Run across all Python versions to find compatibility issues

The same uniform approach works for any scientific Python extension!
