#!/bin/bash
# Build script for arraysum extension
# Usage: ./build_extension.sh <python_executable>

PYTHON=${1:-python}

# Get paths - use distutils for better venv compatibility
PYTHON_INC=$($PYTHON -c "import distutils.sysconfig; print(distutils.sysconfig.get_python_inc())")
NUMPY_INC=$($PYTHON -c "import numpy; print(numpy.get_include())")
F2PY_SRC=$($PYTHON -c "import numpy; import os; print(os.path.join(os.path.dirname(numpy.__file__), 'f2py', 'src'))")

# Generate wrapper
$PYTHON -m numpy.f2py arraysum.pyf

# Compile
gcc -shared -fPIC \
    -I"$PYTHON_INC" \
    -I"$NUMPY_INC" \
    -I"$F2PY_SRC" \
    arraysummodule.c arraysum.c "$F2PY_SRC/fortranobject.c" \
    -o arraysum.so

echo "Built arraysum.so for $PYTHON"
