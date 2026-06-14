#!/bin/bash
set -e

PYTHON=${1:-python3}
CONTAINER=${2:-ubuntu24.04.sif}

echo "=============================================================="
echo "Testing with: $PYTHON in $CONTAINER"
echo "=============================================================="

# Copy test_extension into container and run tests
apptainer exec "$CONTAINER" bash << INNER_SCRIPT
cd /tmp
cp -r /home/worker/snakepit/test_extension .

cd test_extension
bash run_tests.sh "$PYTHON"
INNER_SCRIPT

echo ""
echo "=============================================================="
echo "Test completed successfully with $PYTHON"
echo "=============================================================="
