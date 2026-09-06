#!/bin/bash
# Build script for arraysum extension
# Usage: ./build_extension.sh <python_executable>

PYTHON=${1:-python}

# Get paths - use sysconfig, then verify
PYTHON_INC=$($PYTHON -c "import sysconfig; print(sysconfig.get_path('include'))")
NUMPY_INC=$($PYTHON -c "import numpy; print(numpy.get_include())")
F2PY_SRC=$($PYTHON -c "import numpy; import os; print(os.path.join(os.path.dirname(numpy.__file__), 'f2py', 'src'))")

# If Python.h is not found, try alternate paths. PyPy is checked separately
# and first: a container may have both a native CPython and a PyPy of the
# same X.Y version (e.g. 2.7), and /usr/include/pythonX.Y belongs to CPython
# -- letting PyPy fall into that branch silently builds against the wrong
# Python.h (CPython's), which compiles fine but fails at import time with
# "undefined symbol" errors, since PyPy's cpyext ABI needs its own headers.
if [ ! -f "$PYTHON_INC/Python.h" ]; then
    IMPL=$($PYTHON -c "import platform; print(platform.python_implementation())")
    if [ "$IMPL" = "PyPy" ]; then
        # PyPy venvs may not inherit the base include path; use base_prefix
        BASE_INC=$($PYTHON -c "import sys, os; print(os.path.join(sys.base_prefix, 'include'))" 2>/dev/null || true)
        if [ -n "$BASE_INC" ] && [ -f "$BASE_INC/Python.h" ]; then
            PYTHON_INC="$BASE_INC"
        fi
    else
        PYVER=$($PYTHON -c "import sys; print('python' + str(sys.version_info[0]) + '.' + str(sys.version_info[1]))")
        if [ -d "/usr/include/$PYVER" ]; then
            PYTHON_INC="/usr/include/$PYVER"
        fi
    fi
fi

# Generate wrapper
$PYTHON -m numpy.f2py arraysum.pyf

# Determine the correct extension suffix for this Python
EXT_SUFFIX=$($PYTHON -c "import sysconfig; print(sysconfig.get_config_var('SO') or '.so')")

# PyPy doesn't export its C-API symbols to the running process the way
# CPython does, so extensions must link libpypy-c.so explicitly (with an
# rpath, since it usually isn't on the default library search path).
# CPython extensions resolve symbols against the process instead and need
# none of this.
LINK_FLAGS=""
IMPL=$($PYTHON -c "import platform; print(platform.python_implementation())")
if [ "$IMPL" = "PyPy" ]; then
    PYPY_REAL=$($PYTHON -c "import sys, os; print(os.path.realpath(sys.executable))")
    PYPY_LIBDIR=$(dirname "$PYPY_REAL")
    PYPY_LIB=$(ls "$PYPY_LIBDIR"/libpypy*-c.so 2>/dev/null | head -1)
    if [ -n "$PYPY_LIB" ]; then
        PYPY_LIBNAME=$(basename "$PYPY_LIB" .so)
        PYPY_LIBNAME=${PYPY_LIBNAME#lib}
        LINK_FLAGS="-L$PYPY_LIBDIR -l$PYPY_LIBNAME -Wl,-rpath,$PYPY_LIBDIR"
    fi
fi

# Compile
gcc -shared -fPIC \
    -I"$PYTHON_INC" \
    -I"$NUMPY_INC" \
    -I"$F2PY_SRC" \
    arraysummodule.c arraysum.c "$F2PY_SRC/fortranobject.c" \
    $LINK_FLAGS \
    -o "arraysum${EXT_SUFFIX}"

echo "Built arraysum${EXT_SUFFIX} for $PYTHON"
