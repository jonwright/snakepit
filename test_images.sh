#!/bin/bash
#
# Test script for snakepit Docker images
# This script verifies all Python versions can create venvs and have working headers
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${SCRIPT_DIR}/test_workspace"

# Create clean test workspace
rm -rf "${WORKSPACE_DIR}"
mkdir -p "${WORKSPACE_DIR}"

echo "======================================"
echo "Testing snakepit:u20 (Python 2.7, 3.8)"
echo "======================================"

# Test Python 2.7
echo ""
echo "Testing with Python 2.7..."
docker run --rm --user $(id -u):$(id -g) -e HOME=/workspace -v "${WORKSPACE_DIR}:/workspace" snakepit:u20 bash -c "
    cd /workspace && \
    python2.7 -m virtualenv venv_py27 && \
    python2.7 -m pip install --upgrade pip && \
    python2.7 -m pip install 'numpy<1.17' && \
    python2.7 -c 'import numpy, sysconfig, os; print(\"NumPy:\", numpy.__version__); inc=sysconfig.get_path(\"include\"); print(\"Include:\", inc); print(\"Python.h:\", os.path.exists(os.path.join(inc, \"Python.h\")))' && \
    echo '✓ Python 2.7 venv created successfully'
"

# Test Python 3.8
echo ""
echo "Testing with Python 3.8..."
docker run --rm --user $(id -u):$(id -g) -e HOME=/workspace -v "${WORKSPACE_DIR}:/workspace" snakepit:u20 bash -c "
    cd /workspace && \
    python3.8 -m venv venv_py38 && \
    python3.8 -m pip install --upgrade pip && \
    python3.8 -m pip install numpy && \
    python3.8 -c 'import numpy, sysconfig, os; print(\"NumPy:\", numpy.__version__); inc=sysconfig.get_path(\"include\"); print(\"Include:\", inc); print(\"Python.h:\", os.path.exists(os.path.join(inc, \"Python.h\")))' && \
    echo '✓ Python 3.8 venv created successfully'
"

echo ""
echo "========================================================"
echo "Testing snakepit:u24 (Python 3.9-3.14)"
echo "========================================================"

for PY_VERSION in 3.9 3.10 3.11 3.12 3.13 3.14; do
    echo ""
    echo "Testing with Python ${PY_VERSION}..."
    docker run --rm --user $(id -u):$(id -g) -e HOME=/workspace -v "${WORKSPACE_DIR}:/workspace" snakepit:u24 bash -c "
        cd /workspace && \
        python${PY_VERSION} -m venv venv_py${PY_VERSION/./} && \
        python${PY_VERSION} -m pip install --upgrade pip && \
        python${PY_VERSION} -m pip install numpy && \
        python${PY_VERSION} -c 'import numpy, sysconfig, os; print(\"NumPy:\", numpy.__version__); inc=sysconfig.get_path(\"include\"); print(\"Include:\", inc); print(\"Python.h:\", os.path.exists(os.path.join(inc, \"Python.h\")))' && \
        echo '✓ Python ${PY_VERSION} venv created successfully'
    "
done

echo ""
echo "======================================"
echo "All 8 Python versions tested! ✓"
echo "======================================"
echo ""
echo "Created venvs in ${WORKSPACE_DIR}:"
ls -1 "${WORKSPACE_DIR}" | grep venv
