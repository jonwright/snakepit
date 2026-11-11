#!/bin/bash
#SBATCH --job-name=snakepit-p9
#SBATCH --partition=low-p9gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=build_p9-%j.log
#
# Build and test snakepit-p9.sif natively on a POWER9 node, in one command:
#
#     sbatch build_p9.sh          (from the snakepit checkout)
#
# Builds in node-local /tmp, runs test_images.py there (only the ppc64le
# entries run; others are skipped by architecture), and only if every test
# passes copies snakepit-p9.sif and test_results_p9.log into the checkout.
# The /tmp work directory is always removed.

set -u
REPO=${SLURM_SUBMIT_DIR:-$(cd "$(dirname "$0")" && pwd)}
WORK=$(mktemp -d "${TMPDIR:-/tmp}/snakepit-p9.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

echo "host=$(hostname) arch=$(uname -m) repo=$REPO work=$WORK"
[ "$(uname -m)" = ppc64le ] || { echo "ERROR: run this on a POWER9 (ppc64le) node"; exit 1; }

mkdir -p "$WORK/ctx" "$WORK/tmp" "$WORK/cache" "$WORK/test"
cp "$REPO/snakepit-p9.def" "$REPO/install_sci_packages.sh" "$WORK/ctx/"
export APPTAINER_TMPDIR=$WORK/tmp APPTAINER_CACHEDIR=$WORK/cache

cd "$WORK/ctx"
start=$(date +%s)
if ! apptainer build --fakeroot "$WORK/snakepit-p9.sif" snakepit-p9.def > "$WORK/build.log" 2>&1; then
    echo "ERROR: build failed after $(( $(date +%s) - start ))s; last lines:"
    tail -40 "$WORK/build.log"
    exit 1
fi
echo "build OK in $(( $(date +%s) - start ))s, $(du -m "$WORK/snakepit-p9.sif" | cut -f1) MB"
apptainer exec -e "$WORK/snakepit-p9.sif" cat /opt/snakepit/packages.txt

cp -r "$REPO/test_images.py" "$REPO/test_extension" "$WORK/test/"
ln -s "$WORK/snakepit-p9.sif" "$WORK/test/snakepit-p9.sif"
cd "$WORK/test"
if ! python3 test_images.py > run.log 2>&1; then
    echo "ERROR: tests failed; image NOT installed"
    grep -E "^\[OK\]|^\[FAIL\]|Results:" run.log | tail -20
    cp test_results.log "$REPO/test_results_p9.log"
    exit 1
fi
grep -E "^\[OK\] Python|Results:" run.log

cp test_results.log "$REPO/test_results_p9.log"
# If snakepit-p9.sif is a symlink (e.g. to an image store), replace its target.
DEST=$(readlink -f "$REPO/snakepit-p9.sif")
cp "$WORK/snakepit-p9.sif" "$DEST.new" && mv -f "$DEST.new" "$DEST"
echo "installed $DEST"
