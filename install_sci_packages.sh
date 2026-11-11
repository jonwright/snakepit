#!/bin/bash
# Install numpy, numba, h5py into each interpreter's *system* site-packages
# at image build time, so downstream users can opt in with
#   python3.X -m venv --system-site-packages ...   (or virtualenv / uv venv)
# or ignore them with a plain venv.
#
# Usage: install_sci_packages.sh PY [PY ...]
#
# Rules: wheels only (never build upstream packages from source). A package
# with no wheel for an interpreter is skipped and shows as "-" in the
# manifest /opt/snakepit/packages.txt. Missing interpreters are skipped.

MANIFEST=/opt/snakepit/packages.txt
NIGHTLY_INDEX="https://pypi.anaconda.org/scientific-python-nightly-wheels/simple"
mkdir -p /opt/snakepit

export PIP_BREAK_SYSTEM_PACKAGES=1   # Debian/Ubuntu EXTERNALLY-MANAGED; old pips ignore it
export PIP_ROOT_USER_ACTION=ignore
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_CACHE_DIR=1

UV=$(command -v uv || ls /root/.local/bin/uv 2>/dev/null || true)

install_one() {
    # install_one PY PKG [extra args...]
    local py=$1 pkg=$2; shift 2
    local ver
    ver=$("$py" -c 'import sys; print("%d%d" % sys.version_info[:2])')
    if [ -n "$UV" ] && [ "$ver" -ge 38 ] && [ "${ver:0:1}" = 3 ]; then
        # uv needs no pip inside the target interpreter
        "$UV" pip install --no-cache --python "$py" --system --break-system-packages \
            --only-binary :all: "$@" "$pkg"
    else
        "$py" -m pip install --only-binary :all: "$@" "$pkg"
    fi
}

for PY in "$@"; do
    if ! command -v "$PY" >/dev/null 2>&1; then
        echo "[skip] $PY not found"
        continue
    fi
    echo "=== $PY: installing numpy/numba/h5py (wheels only)"
    install_one "$PY" numpy  || echo "[no wheel] numpy for $PY"
    install_one "$PY" numba  || echo "[no wheel] numba for $PY"
    case "$PY" in
        python3.15*)
            # h5py releases have no cp315 wheels until h5py 3.17.0 (h5py #2993):
            # use h5py's own nightly *wheels*. Remove once 3.17.0 is on PyPI.
            if [ -n "$UV" ]; then
                install_one "$PY" h5py --prerelease allow --extra-index-url "$NIGHTLY_INDEX"
            else
                install_one "$PY" h5py --pre --extra-index-url "$NIGHTLY_INDEX"
            fi || echo "[no wheel] h5py for $PY" ;;
        *)
            install_one "$PY" h5py || echo "[no wheel] h5py for $PY" ;;
    esac
done

# Manifest: what actually imports in each interpreter
: > "$MANIFEST"
for PY in "$@"; do
    command -v "$PY" >/dev/null 2>&1 || continue
    "$PY" - "$PY" >> "$MANIFEST" 2>/dev/null <<'EOF'
import sys
out = []
for m in ("numpy", "numba", "h5py"):
    try:
        out.append("%s=%s" % (m, __import__(m).__version__))
    except Exception:
        out.append("%s=-" % m)
print("%-12s %-10s %s" % (sys.argv[1], sys.version.split()[0], " ".join(out)))
EOF
done
echo "--- $MANIFEST"
cat "$MANIFEST"
