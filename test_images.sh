#!/bin/bash
#
# Test script for snakepit Docker images
# This script tests building a C extension with f2py across different Python versions
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_EXT_DIR="${SCRIPT_DIR}/../test_extension"

echo "======================================"
echo "Testing snakepit:u20 (Python 2.7, 3.8)"
echo "======================================"

# Test Python 2.7
echo ""
echo "Testing with Python 2.7..."
docker run --rm -v "${TEST_EXT_DIR}:/work" -w /work snakepit:u20 bash -c "
    python2.7 -m venv venv_py27 && \
    . venv_py27/bin/activate && \
    pip install numpy && \
    ./build_extension.sh && \
    python -c 'import arraysum; import numpy as np; result = arraysum.arraysum([1,2,3], [4,5,6]); print(\"Result: {}\".format(result)); assert np.array_equal(result, [5,7,9])' && \
    echo '✓ Python 2.7 test passed'
"

# Test Python 3.8
echo ""
echo "Testing with Python 3.8..."
docker run --rm -v "${TEST_EXT_DIR}:/work" -w /work snakepit:u20 bash -c "
    python3.8 -m venv venv_py38 && \
    . venv_py38/bin/activate && \
    pip install numpy scipy && \
    ./build_extension.sh && \
    python -c 'import arraysum; import numpy as np; result = arraysum.arraysum([1,2,3], [4,5,6]); print(f\"Result: {result}\"); assert np.array_equal(result, [5,7,9])' && \
    echo '✓ Python 3.8 test passed'
"

echo ""
echo "======================================"
echo "Testing snakepit:u24 (Python 3.12)"
echo "======================================"

# Test Python 3.12
echo ""
echo "Testing with Python 3.12..."
docker run --rm -v "${TEST_EXT_DIR}:/work" -w /work snakepit:u24 bash -c "
    python3.12 -m venv venv_py312 && \
    . venv_py312/bin/activate && \
    pip install numpy scipy && \
    ./build_extension.sh && \
    python -c 'import arraysum; import numpy as np; result = arraysum.arraysum([1,2,3], [4,5,6]); print(f\"Result: {result}\"); assert np.array_equal(result, [5,7,9])' && \
    echo '✓ Python 3.12 test passed'
"

echo ""
echo "======================================"
echo "All tests passed! ✓"
echo "======================================"
