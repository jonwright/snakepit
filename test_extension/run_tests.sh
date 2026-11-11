#!/bin/bash
# Unified test script for all Python versions
# Usage: run_tests.sh <python_command>
# Example: run_tests.sh python2.7
#          run_tests.sh python3.11
#          run_tests.sh python3.14t

set -e

# Apptainer bind-mounts $HOME, and venvs made with --system-site-packages
# re-enable ~/.local/lib/pythonX.Y/site-packages. Without this, the host
# user's own numpy etc. silently shadow the image's packages.
export PYTHONNOUSERSITE=1

PYTHON_CMD=${1:-python}
MODE=${2:-}  # Optional: "preinstalled" (system packages) or "bare" (no packages)
# Never build upstream packages from source: wheels only. A package with no
# wheel for this interpreter is skipped (h5py/numba are optional; numpy is not).
ONLY_BINARY="--only-binary :all:"
# Released h5py has no cp315 wheels yet (due in h5py 3.17.0, h5py issue #2993);
# take h5py's own nightly *wheels* for 3.15/3.15t until then. Remove once
# h5py 3.17.0 is on PyPI.
NIGHTLY_INDEX="https://pypi.anaconda.org/scientific-python-nightly-wheels/simple"
H5PY_PIP_EXTRA=""
H5PY_UV_EXTRA=""
if [[ "${PYTHON_CMD}" == python3.15* ]]; then
    H5PY_PIP_EXTRA="--pre --extra-index-url ${NIGHTLY_INDEX}"
    H5PY_UV_EXTRA="--prerelease allow --extra-index-url ${NIGHTLY_INDEX}"
fi
# Extract version for unique venv directory (e.g., python2.7 -> venv_27)
PYTHON_VER=$(echo "${PYTHON_CMD}" | sed 's/python//' | sed 's/\.//')
VENV_DIR="venv_${PYTHON_VER}"

echo "========================================================================"
echo "Setting up test environment with ${PYTHON_CMD}"
echo "========================================================================"

# Remove stale venv if present
rm -rf ${VENV_DIR}

# Create virtual environment. "preinstalled" exposes the image's
# numpy/numba/h5py (installed by install_sci_packages.sh) to the venv.
SYS_SITE=""
[[ "${MODE}" == "preinstalled" ]] && SYS_SITE="--system-site-packages"
if [[ "${PYTHON_CMD}" == pypy2* || "${PYTHON_CMD}" == *"2.7"* ]]; then
    ${PYTHON_CMD} -m virtualenv ${SYS_SITE} ${VENV_DIR}
elif [[ "${PYTHON_CMD}" == pypy3* || "${PYTHON_CMD}" == *"t" ]] && \
        PATH="/root/.local/bin:$PATH" command -v uv >/dev/null 2>&1; then
    # uv-managed interpreters (PyPy 3, free-threading builds)
    export PATH="/root/.local/bin:$PATH"
    # Absolute path: a bare name lets uv pick a uv-managed Python from the
    # host user's bind-mounted ~/.local/share/uv instead of the image's.
    uv venv --python "$(command -v ${PYTHON_CMD})" ${SYS_SITE} ${VENV_DIR}
else
    ${PYTHON_CMD} -m venv ${SYS_SITE} ${VENV_DIR}
fi
source ${VENV_DIR}/bin/activate

if [[ "${MODE}" == "bare" ]]; then
    # Pre-release interpreter with no upstream wheels yet: check the
    # interpreter and its venv only, no numpy/h5py/numba/f2py.
    python -c "import sys, sysconfig; print('Python ' + sys.version); print('Py_GIL_DISABLED=' + str(sysconfig.get_config_var('Py_GIL_DISABLED')))"
    python -c "import ssl, sqlite3, ctypes, zlib, json; print('stdlib imports OK')"
    echo ""
    echo "========================================================================"
    echo "Bare interpreter checks PASSED for ${PYTHON_CMD} (no packages tested)"
    echo "========================================================================"
    exit 0
fi

# Install dependencies from requirements.txt
echo ""
echo "Installing packages from requirements.txt..."
if [[ "${MODE}" == "preinstalled" ]]; then
    echo "Using pre-installed system packages (no pip install needed)"
elif [[ "${PYTHON_CMD}" == *"t" ]]; then
    # uv-managed Python: install packages individually so optional ones don't
    # block required ones (e.g. numba may not support pre-release Python versions)
    set +e
    uv pip install ${ONLY_BINARY} numpy --quiet
    uv pip install ${ONLY_BINARY} ${H5PY_UV_EXTRA} h5py --quiet
    uv pip install ${ONLY_BINARY} numba --quiet
    set -e
elif [[ "${PYTHON_CMD}" == pypy3* ]]; then
    set +e
    uv pip install ${ONLY_BINARY} numpy --quiet
    uv pip install ${ONLY_BINARY} h5py --quiet
    uv pip install ${ONLY_BINARY} numba --quiet
    set -e
else
    python -m pip install --upgrade pip --quiet
    # Install packages individually so optional ones (h5py, numba) don't
    # block required ones (numpy) when source builds are needed
    set +e
    python -m pip install ${ONLY_BINARY} numpy --quiet
    python -m pip install ${ONLY_BINARY} ${H5PY_PIP_EXTRA} h5py --quiet
    python -m pip install ${ONLY_BINARY} numba --quiet
    set -e
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
