#!/bin/bash
# Unified test script for all Python versions
# Usage: run_tests.sh <python_command>
# Example: run_tests.sh python2.7
#          run_tests.sh python3.11

set -e

PYTHON_CMD=${1:-python}
# Extract version for unique venv directory (e.g., python2.7 -> venv_27)
PYTHON_VER=$(echo "${PYTHON_CMD}" | sed 's/python//' | sed 's/\.//')
VENV_DIR="venv_${PYTHON_VER}"

echo "========================================================================"
echo "Setting up test environment with ${PYTHON_CMD}"
echo "========================================================================"

# Create virtual environment
if [[ "${PYTHON_CMD}" == *"2.7"* ]]; then
    ${PYTHON_CMD} -m virtualenv ${VENV_DIR}
else
    ${PYTHON_CMD} -m venv ${VENV_DIR}
fi

# Activate venv
source ${VENV_DIR}/bin/activate

# Install dependencies from requirements.txt
echo ""
echo "Installing packages from requirements.txt..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

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
