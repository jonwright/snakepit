#!/bin/bash
# Run test_extension/run_tests.sh for one interpreter in one image.
#
#   ./test_in_container.sh PYTHON IMAGE.sif [preinstalled|fresh|bare]
#   ./test_in_container.sh python3.12 snakepit-modern.sif
#
# preinstalled (default): venv --system-site-packages, uses the image's
#   numpy/numba/h5py. fresh: empty venv, installs wheels. bare: stdlib only.
# Works on a copy in a temporary directory, removed afterwards.
set -e
PYTHON=${1:?usage: $0 PYTHON IMAGE.sif [preinstalled|fresh|bare]}
SIF=${2:?usage: $0 PYTHON IMAGE.sif [preinstalled|fresh|bare]}
MODE=${3:-preinstalled}
[ "$MODE" = fresh ] && MODE=""
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(mktemp -d "${TMPDIR:-/tmp}/snakepit-test.XXXXXX")
trap 'rm -rf "$W"' EXIT
cp -r "$HERE/test_extension/." "$W/"
apptainer exec -e -B "$W:/workspace" --pwd /workspace "$SIF" \
    bash -c "bash run_tests.sh $PYTHON $MODE"
