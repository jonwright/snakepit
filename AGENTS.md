# Snakepit Project Context for AI Agents

## 7-Bit ASCII Encoding Requirement

**IMPORTANT**: All source files in this repository MUST use only 7-bit ASCII encoding (bytes 0-127). 

### Rationale
- Ensures maximum compatibility with legacy systems and HPC environments
- Prevents encoding issues in container environments
- Simplifies cross-platform text processing

### What This Means

**DO NOT USE:**
- Unicode characters (emoji, special symbols, smart quotes, box-drawing chars)
- Non-ASCII accented characters
- Unicode arrows, checkmarks, mathematical symbols, etc.

**EXAMPLES OF WHAT TO REPLACE:**
- checkmark symbol -> `[OK]` or `OK`
- cross/multiplication symbol -> `[FAIL]` or `FAIL`
- arrow symbol -> `>>` or `-->`
- snake emoji -> remove or spell out `snake`
- box-drawing chars (e.g. tree branches) -> `|--`, `` `--`
- em dash -> `-` (hyphen)
- smart quotes -> `"` (regular quotes)

### Files Modified for ASCII Compliance
- README.md: Removed emoji, replaced checkmarks with [OK]
- SUMMARY.md: Box-drawing characters --> ASCII tree format
- specification.md: Box-drawing characters --> ASCII format
- test_images.py: Unicode symbols --> ASCII markers
- test_results.log: Unicode symbols --> ASCII markers

### Verification

To verify ASCII compliance:
```bash
python3 << 'EOF'
import os
with open('filename.txt', 'rb') as f:
    content = f.read()
    non_ascii = [b for b in content if b > 127]
    if non_ascii:
        print("Contains non-ASCII bytes")
    else:
        print("7-bit ASCII compliant")
EOF
```

## Project Overview

Snakepit is a multi-Python Apptainer container testing suite for scientific Python C extensions.

### Quick Commands

### Native (x86_64) Containers

Build containers (no sudo required - uses fakeroot):
```bash
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

Three containers (consolidated from an earlier six -- see git history).
Every interpreter is a binary from a package manager (apt, deadsnakes PPA,
uv/python-build-standalone, or pypy.org) -- never compiled from source here.

### Cross-Architecture Containers (ppc64le / aarch64)

Builds foreign-architecture containers using QEMU user-mode emulation.
Requires `qemu-user-static` on the build host.

**Sysadmin setup** (one-time):
```bash
# Debian/Ubuntu host:
sudo apt-get install -y qemu-user-static

# RHEL/CentOS/Fedora host:
sudo dnf install -y qemu-user-static

# Verify binfmt_misc handlers are registered:
ls /proc/sys/fs/binfmt_misc/ | grep qemu
# Should show: qemu-aarch64  qemu-ppc64le  (among others)
```

**Build commands** (the --arch flag tells Apptainer which Docker image variant to pull):
```bash
apptainer build --fakeroot --arch ppc64le ubuntu20.04_ppc64le.sif ubuntu20.04_ppc64le.def
apptainer build --fakeroot --arch arm64 ubuntu24.04_aarch64.sif ubuntu24.04_aarch64.def
```

**How it works**: QEMU user-mode + kernel binfmt_misc handlers translate foreign
architecture binaries transparently. Apptainer's `--arch` flag selects the matching
Docker image variant. Both build-time (%post scripts) and runtime (`apptainer exec`)
are emulated -- no native hardware required.

Test a Python version:
```bash
./test_in_container.sh python3.11 snakepit-manylinux2014.sif
```

### Supported Python Versions
- **snakepit-legacy.sif** (Ubuntu 18.04): Python 2.7, 3.6, 3.7 (native apt), 3.8 (uv prebuilt),
  PyPy 2.7 (pypy.org tarball), PyPy 3.9 (uv prebuilt)
- **snakepit-manylinux2014.sif** (CentOS 7, glibc 2.17): Python 3.9, 3.10, 3.11, PyPy 3.11
  -- **tested versions only**. The image also ships 3.12-3.15/3.14t/3.15t
  interpreters, but numpy has no manylinux2014 wheels for cp312+ and this
  image's GCC 10.2 can't build numpy from source (needs >= 10.3), so those
  are NOT in the test matrix. Use `snakepit-modern.sif` for those.
- **snakepit-modern.sif** (Ubuntu 24.04): Python 3.9, 3.10, 3.11 (deadsnakes PPA),
  3.12 (native default), 3.13, 3.14, 3.15 (deadsnakes PPA), 3.14t, 3.15t
  (uv prebuilt free-threading). 3.9/3.10/3.11 are tested here *and* in
  `snakepit-manylinux2014.sif` on purpose -- the original six-container
  design tested those three versions against both a modern and an old glibc
  baseline, and this preserves that.
- **ubuntu20.04_ppc64le.sif**: Python 3.11 (Power9 / ppc64le, QEMU build)
- **ubuntu24.04_aarch64.sif**: Python 3.11 (ARM64 / aarch64, QEMU build)

**Fixed issue**: putting PyPy 2.7 in the same container as native CPython 2.7
(`snakepit-legacy.sif`) exposed a bug in `test_extension/build_extension.sh`: its
header-path fallback picked up CPython's `/usr/include/python2.7` before
trying PyPy's own include dir, since both now coexist in one container.
Fixed by checking `platform.python_implementation()` first and giving PyPy
its own header/link path (it also needs an explicit `-lpypy-c` link with an
rpath, unlike CPython). See `specification.md` under "PyPy 2.7".

**Note: Python 3.16** is in alpha (3.16.0a1 on deadsnakes noble, a2 via uv as of
2026-11). `snakepit-modern.def` installs 3.16/3.16t optionally; beta 1 is expected
May 2027. Until numpy/h5py/numba publish cp316 wheels, 3.16/3.16t are tested as
bare interpreters (`BARE_VERSIONS` in `test_images.py`: venv + stdlib only).

**Rule: never build upstream packages from source.** `run_tests.sh` installs
numpy/h5py/numba with `--only-binary :all:`. If a package has no wheel for an
interpreter, it is skipped (h5py, numba) or that version is tested bare (numpy).
Only exception: a version that already depended on a source build before this
rule (record it here if one turns up). Pre-release *wheels* are allowed:
3.15/3.15t take h5py from the scientific-python nightly wheel index until
h5py 3.17.0 ships cp315 wheels (h5py issue #2993). 3.16t has no h5py wheel at
all, and numpy has no cp316 wheels even as nightlies, so 3.16/3.16t stay bare.

**Preinstalled packages**: `install_sci_packages.sh` (run at build time) puts
numpy/numba/h5py wheels into every interpreter's system site-packages; see
`/opt/snakepit/packages.txt` in each image for what is present ("-" = no wheel).
Downstream opts in with `venv --system-site-packages` (or `virtualenv`/`uv venv`
with the same flag), or uses a plain venv to ignore them. Apptainer mounts
$HOME, so: set `PYTHONNOUSERSITE=1` (else ~/.local/lib/pythonX.Y packages
shadow the image's) and give `uv venv --python` an absolute interpreter path
(else uv may pick a Python from the host's ~/.local/share/uv). `run_tests.sh`
does both. PyPy 2.7 and PyPy 3.11 (manylinux2014) have no numpy wheels and
currently fail the matrix.

### Key Files
- `snakepit-legacy.def` / `snakepit-manylinux2014.def` / `snakepit-modern.def`: Apptainer container definitions
- `ubuntu20.04_ppc64le.def` / `ubuntu24.04_aarch64.def`: Cross-architecture definitions (QEMU)
- `test_in_container.sh`: Primary test runner script
- `test_extension/`: Example C extension with NumPy f2py
- `test_images.py`: Automated container test suite
- `SKILL.md`: Detailed container usage guide for AI agents

### Architecture
- Apptainer definitions use fakeroot for non-root container building
- Tests are Python 2.7-3.15 compatible (no f-strings, `from __future__ import`)
- Single `requirements.txt` with Python version markers handles all package versions

## Contributing Guidelines

When adding or modifying files:
1. **Always use 7-bit ASCII encoding** - no unicode characters
2. Keep container definitions minimal and focused on build/runtime requirements
3. Test across all supported Python versions: `python test_images.py`
4. Update README.md if adding new features
5. Maintain backward compatibility with Python 2.7 in test code

## Testing
Run all tests:
```bash
python3 test_images.py
```

This builds all containers and tests all Python versions. Results are logged to `test_results.log`.

## Notes for LLM/AI Agents

- Prefer conciseness in comments; avoid redundant documentation
- Keep functions focused and minimal
- Test code should work identically across Python 2.7-3.15
- Use `from __future__ import print_function` for Python 2.7 compatibility
- No f-strings in any Python code that must support Python 2.7
- PyPy uses `virtualenv` (not `venv`); `ensurepip` bootstraps pip on PyPy
- See `SKILL.md` for a detailed walkthrough of using these containers, including build commands, testing, and adding new Python versions.

## Container Usage Quick Reference

### Build Containers
```bash
apptainer build --fakeroot <name>.sif <name>.def
```

### Run a Command
```bash
apptainer exec <image>.sif python3.X -c "print('hello')"
```

### Interactive Shell with Volume Mount
```bash
apptainer exec --bind $(pwd):/workspace <image>.sif bash
```

### Test a Python Version
```bash
./test_in_container.sh python3.X <image>.sif
```

### Run Full Test Suite
```bash
python3 test_images.py
```

### Add a New Python Version (4-Step Checklist)
1. Add `python3.X python3.X-dev python3.X-venv` to the `.def` file's apt install block
2. Add `("3.X", "<container>.sif")` to `PYTHON_VERSIONS` in `test_images.py`
3. Rebuild the container: `apptainer build --fakeroot <container>.sif <container>.def`
4. Run the test suite: `python3 test_images.py`
