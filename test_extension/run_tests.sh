#!/bin/bash
# Unified test script for all Python versions
# Usage: run_tests.sh <python_command>
# Example: run_tests.sh python2.7
#          run_tests.sh python3.11
#          run_tests.sh python3.14t

set -e

PYTHON_CMD=${1:-python}
# Extract version for unique venv directory (e.g., python2.7 -> venv_27)
PYTHON_VER=$(echo "${PYTHON_CMD}" | sed 's/python//' | sed 's/\.//')
VENV_DIR="venv_${PYTHON_VER}"

echo "========================================================================"
echo "Setting up test environment with ${PYTHON_CMD}"
echo "========================================================================"

# Remove stale venv if present
rm -rf ${VENV_DIR}

# Create virtual environment
if [[ "${PYTHON_CMD}" == *"2.7"* ]]; then
    ${PYTHON_CMD} -m virtualenv ${VENV_DIR}
    source ${VENV_DIR}/bin/activate
elif [[ "${PYTHON_CMD}" == *"t" ]]; then
    # Free-threading Python: use uv for venv and pip
    export PATH="/root/.local/bin:$PATH"
    uv venv --python ${PYTHON_CMD} ${VENV_DIR}
    source ${VENV_DIR}/bin/activate
else
    ${PYTHON_CMD} -m venv ${VENV_DIR}
    source ${VENV_DIR}/bin/activate
fi

# Install dependencies from requirements.txt
echo ""
echo "Installing packages from requirements.txt..."
if [[ "${PYTHON_CMD}" == *"t" ]]; then
    # uv-managed Python: use uv pip install (no ensurepip in python-build-standalone)
    uv pip install -r requirements.txt --quiet
else
    python -m pip install --upgrade pip --quiet
    python -m pip install -r requirements.txt --quiet
fi

# Build C extension with f2py
echo ""
echo "Building C extension with f2py..."
bash build_extension.sh python

# Run tests
echo ""
python test_uniform.py

# Report success
echo ""
echo "========================================================================"
echo "All tests PASSED for ${PYTHON_CMD}"
echo "========================================================================"
