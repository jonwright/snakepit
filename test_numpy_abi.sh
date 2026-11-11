#!/bin/bash
#SBATCH --job-name=snakepit-npabi
#SBATCH --partition=nice
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=test_numpy_abi-%j.log
#
# numpy 1 vs 2 extension ABI check, x86_64 (one command, from the checkout):
#
#     sbatch test_numpy_abi.sh  [NP1_PYTHON]
#     srun -p nice bash test_numpy_abi.sh  [NP1_PYTHON]
#
# NP1_PYTHON is a Python with numpy 1.x and a matching gcc on the host;
# default: the ESRF `module load jupyter-slurm` environment (3.12, numpy 1.26).
# The numpy 2 side is python3.12 in snakepit-modern.sif.
#
#   A  native: test_extension/run_tests.sh against NP1_PYTHON's own packages
#   B  build with numpy 2, import with numpy 1   -> must work
#   C  build with numpy 1, import with numpy 2   -> must FAIL (one-way ABI)
#
# Any other outcome exits 1. Work happens in a /tmp dir that is removed.

set -u
REPO=${SLURM_SUBMIT_DIR:-$(cd "$(dirname "$0")" && pwd)}
NP1=${1:-/cvmfs/hpc.esrf.fr/software/packages/linux/x86_64/jupyter-slurm/latest/envs/jupyter-slurm/bin/python}
SIF=$REPO/snakepit-modern.sif
export PYTHONNOUSERSITE=1
W=$(mktemp -d "${TMPDIR:-/tmp}/npabi.XXXXXX"); trap 'rm -rf "$W"' EXIT
NP1_BIN=$(dirname "$NP1")
in_sif() { apptainer exec -e --env PYTHONNOUSERSITE=1 "$SIF" bash -c "$1"; }
npver() { "$1" -c 'import sys, numpy; print(sys.version.split()[0], "numpy", numpy.__version__)'; }

echo "host=$(hostname) np1=$NP1 ($(npver "$NP1"))"
for d in A B C; do cp -r "$REPO/test_extension" "$W/$d"; done
rc=0

echo "### A: native numpy 1 (run_tests.sh preinstalled)"
if (cd "$W/A" && PATH=$NP1_BIN:$PATH bash run_tests.sh python preinstalled > log 2>&1); then
    echo "[OK] A"; else tail -5 "$W/A/log"; echo "[FAIL] A"; rc=1; fi

echo "### B: build numpy 2 -> run numpy 1 (expect OK)"
cd "$W/B"
in_sif 'bash build_extension.sh python3.12' > log 2>&1
if "$NP1" test_uniform.py >> log 2>&1; then echo "[OK] B"
else tail -5 log; echo "[FAIL] B"; rc=1; fi

echo "### C: build numpy 1 -> run numpy 2 (expect ImportError)"
cd "$W/C"
PATH=$NP1_BIN:$PATH bash build_extension.sh python > log 2>&1
if in_sif 'python3.12 test_uniform.py' >> log 2>&1; then
    echo "[FAIL] C imported: numpy 1 build should not load on numpy 2"; rc=1
elif grep -q "numpy.core.multiarray failed to import" log; then
    echo "[OK] C fails as expected: numpy.core.multiarray failed to import"
else tail -5 log; echo "[FAIL] C failed for another reason"; rc=1; fi

[ $rc = 0 ] && echo "numpy ABI check PASSED" || echo "numpy ABI check FAILED"
exit $rc
