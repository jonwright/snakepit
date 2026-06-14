#!/bin/bash
# Build script for arraysum extension
# Usage: ./build_extension.sh <python_executable>

PYTHON=${1:-python}

# Get paths - use sysconfig, then verify
PYTHON_INC=$($PYTHON -c "import sysconfig; print(sysconfig.get_path('include'))")
NUMPY_INC=$($PYTHON -c "import numpy; print(numpy.get_include())")
F2PY_SRC=$($PYTHON -c "import numpy; import os; print(os.path.join(os.path.dirname(numpy.__file__), 'f2py', 'src'))")

# If Python.h is not found, try alternate paths
if [ ! -f "$PYTHON_INC/Python.h" ]; then
    PYVER=$($PYTHON -c "import sys; print('python' + str(sys.version_info[0]) + '.' + str(sys.version_info[1]))")
    if [ -d "/usr/include/$PYVER" ]; then
        PYTHON_INC="/usr/include/$PYVER"
    fi
fi

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
