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

# PyPy venvs may not inherit the base include path; use base_prefix
if [ ! -f "$PYTHON_INC/Python.h" ]; then
    BASE_INC=$($PYTHON -c "import sys, os; print(os.path.join(sys.base_prefix, 'include'))" 2>/dev/null || true)
    if [ -n "$BASE_INC" ] && [ -f "$BASE_INC/Python.h" ]; then
        PYTHON_INC="$BASE_INC"
    fi
fi

# Generate wrapper
$PYTHON -m numpy.f2py arraysum.pyf

# Determine the correct extension suffix for this Python
EXT_SUFFIX=$($PYTHON -c "import sysconfig; print(sysconfig.get_config_var('SO') or '.so')")

# Compile
gcc -shared -fPIC \
    -I"$PYTHON_INC" \
    -I"$NUMPY_INC" \
    -I"$F2PY_SRC" \
    arraysummodule.c arraysum.c "$F2PY_SRC/fortranobject.c" \
    -o "arraysum${EXT_SUFFIX}"

echo "Built arraysum${EXT_SUFFIX} for $PYTHON"
