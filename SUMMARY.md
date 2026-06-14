# Snakepit: Simplified Uniform Testing Approach

## What We Built

A Docker/Apptainer-based testing environment for Python C extensions that works **uniformly** across Python 2.7 through 3.14 with **no special-casing**.

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
- Works identically from Python 2.7 to 3.14

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

## Test Results

All 8 Python versions tested successfully:

| Python Version | NumPy Version | h5py Version | numba Version | Status |
|----------------|---------------|--------------|---------------|---------|
| 2.7            | 1.16.6        | 2.10.0       | 0.45.0        | [OK] PASSED |
| 3.8            | 1.24.4        | 3.11.0       | 0.58.1        | [OK] PASSED |
| 3.9            | 2.0.2         | 3.14.0       | 0.60.0        | [OK] PASSED |
| 3.10           | 2.2.6         | 3.16.0       | 0.65.1        | [OK] PASSED |
| 3.11           | 2.4.6         | 3.16.0       | 0.65.1        | [OK] PASSED |
| 3.12           | 2.4.6         | 3.16.0       | 0.65.1        | [OK] PASSED |
| 3.13           | 2.4.6         | 3.16.0       | 0.65.1        | [OK] PASSED |
| 3.14           | 2.4.6         | 3.16.0       | 0.65.1        | [OK] PASSED |

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
`-- test_uniform.py     # Python 2.7-3.14 compatible test code
```

## Usage Examples

### Test All Versions

```bash
./test_in_container.sh python3.11 ubuntu24.04.sif
```

### Test One Version

```bash
# Python 2.7
./test_in_container.sh python2.7 ubuntu20.04.sif

# Python 3.13
./test_in_container.sh python3.13 ubuntu24.04.sif
```

### Manual Interactive Testing

```bash
# Enter container
apptainer exec --bind $(pwd)/test_extension:/workspace ubuntu24.04.sif bash

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
