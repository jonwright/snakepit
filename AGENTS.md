# Notes for agents

Read `README.md` first: images, build, test, rules.

## Rules

- 7-bit ASCII only in every file (no emoji, arrows, smart quotes, em
  dashes). Check with:
  `python3 -c "import sys;[sys.exit('NON-ASCII '+f) for f in sys.argv[1:] if any(b>127 for b in open(f,'rb').read())]" FILES`
- Do not compile upstream packages. Use existing binaries (PyPI wheels, silx
  wheelhouse, scientific-python nightlies, conda-forge); install with
  `--only-binary :all:`. If no binary exists, skip the package or test the
  interpreter bare. Compile only to test a git head that has no nightly.
- Test code (`test_extension/`) must run on Python 2.7: no f-strings, use
  `from __future__ import print_function`.
- Images are stored in `/data/id11/jon/snakepit` (GPFS) and symlinked from
  the checkout; `$HOME` is NFS with little space. Build in local `/tmp`, test,
  then copy the image there. POWER9: `sbatch build_p9.sh` (no QEMU for
  ppc64le); it writes through the symlink.

## Pitfalls

- Apptainer mounts `$HOME`: set `PYTHONNOUSERSITE=1`, and pass an absolute
  interpreter path to `uv venv --python`.
- PyPy 3.11 must stay at PyPy 7.3.x (`pypy-3.11.15`); PyPy 8 is ABI pp80 and
  has no numpy wheels.
- PyPy and CPython 2.7 share `snakepit-legacy.sif`; `build_extension.sh`
  checks the implementation before choosing headers, and links PyPy against
  `libpypy*-c.so`.

## Adding a Python version

1. Add the interpreter to the `.def` (from a binary source) and to the
   `install_sci_packages.sh` call in its `%post`.
2. Add `("3.X", "<image>.sif")` to `PYTHON_VERSIONS` in `test_images.py`
   (and to `BARE_VERSIONS` if numpy has no wheel yet).
3. Rebuild, run `python3 test_images.py`, update the README table.

## Files

- `snakepit-*.def`: image definitions; `install_sci_packages.sh`: installs
  numpy/numba/h5py and writes `/opt/snakepit/packages.txt`
- `build_p9.sh`: POWER9 build and test job
- `test_images.py`, `test_in_container.sh`, `test_extension/`: tests
- `test_numpy_abi.sh`: numpy 1 / numpy 2 ABI check
