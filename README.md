# Snakepit

Apptainer images for testing compiled Python extensions (C, f2py) across
Python 2.7 to 3.16, free-threading and PyPy, on several glibc baselines and
on POWER9.

## Images

| Image | Base | Interpreters | Interpreter source |
|---|---|---|---|
| `snakepit-legacy.sif` | Ubuntu 18.04 | 2.7, 3.6, 3.7, 3.8, PyPy 2.7, PyPy 3.9 | apt; uv (3.8, PyPy 3.9); pypy.org (PyPy 2.7) |
| `snakepit-manylinux2014.sif` | CentOS 7, glibc 2.17 | 3.9, 3.10, 3.11 | pypa manylinux2014 image |
| `snakepit-manylinux_2_28.sif` | AlmaLinux 8, glibc 2.28 | 3.9-3.15, 3.14t, 3.15t, PyPy 3.11 | pypa manylinux_2_28 image |
| `snakepit-modern.sif` | Ubuntu 24.04 | 3.9-3.16, 3.14t, 3.15t, 3.16t, PyPy 3.11 | deadsnakes; apt (3.12); uv (t builds, PyPy 3.11) |
| `snakepit-p9.sif` | Ubuntu 24.04, ppc64le | 3.8, 3.11-3.15, 3.14t | conda-forge (micromamba) |

- manylinux2014 is the floor for wheels still tagged manylinux2014; numpy
  stopped publishing such wheels after 2.2.6 and h5py after 3.14.0, so only
  3.9-3.11 are tested there (the image also contains other interpreters).
- manylinux_2_28 is the current floor of the scientific stack (numpy >= 2.3,
  h5py >= 3.15, cibuildwheel >= 3 default). Test wheels tagged manylinux2014
  on both manylinux images.
- 3.16 is an alpha; 3.16, 3.16t and PyPy 2.7 have no numpy wheels and are
  tested as bare interpreters (venv and stdlib only).
- PyPy 3.11 is pinned to PyPy 7.3.23 (ABI pp73); numpy has no wheels for
  PyPy 8 (pp80).
- `snakepit-p9.sif`: PyPI has no ppc64le wheels for numpy, h5py or numba, and
  the silx wheelhouse has no numba, so each Python is a conda-forge
  environment, linked as `/usr/local/bin/python3.X`. python3.8 and python3.11
  are numpy 1 (3.11 is the ESRF jupyter-slurm 2023.10 stack: 3.11.6, numpy
  1.24.4, h5py 3.10.0, numba 0.57.1); the others are numpy 2.
- `ubuntu24.04_aarch64.def` is an old QEMU definition (Python 3.11 only). It
  has not been built or tested with the current scripts.

## Preinstalled packages

Each interpreter has numpy, numba and h5py in its system site-packages where
a binary exists. List them with:

```bash
apptainer exec snakepit-modern.sif cat /opt/snakepit/packages.txt
```

`-` means no binary for that interpreter. A venv made with
`--system-site-packages` uses them; a plain venv does not. Apptainer mounts
`$HOME`, so set `PYTHONNOUSERSITE=1` (or `~/.local` packages shadow the
image's) and give `uv venv --python` an absolute path (or uv may pick a
Python from `~/.local/share/uv`):

```bash
apptainer exec -e snakepit-modern.sif bash -c \
  'python3.12 -m venv --system-site-packages v && PYTHONNOUSERSITE=1 v/bin/python -c "import numpy"'
```

3.15/3.15t take h5py 3.17.0.dev0 from the scientific-python nightly wheels
until h5py 3.17.0 is released.

## Build

x86_64 images, with `--fakeroot` (no sudo):

```bash
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-manylinux_2_28.sif snakepit-manylinux_2_28.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

The current images were built on Ubuntu 20.04. On an Ubuntu 24.04 host with no
`/etc/subuid` entry, the manylinux2014 build fails (Apptainer's injected
`faked` needs a newer glibc than CentOS 7 has). Set `APPTAINER_TMPDIR` and
`APPTAINER_CACHEDIR` to local disk.

POWER9 image, natively on the ESRF `low-p9gpu` partition:

```bash
sbatch build_p9.sh
```

It builds in node-local `/tmp`, runs `test_images.py`, and copies
`snakepit-p9.sif` and `test_results_p9.log` into the checkout only if every
test passes.

## Test

One interpreter (copies `test_extension/` to a temporary directory, builds the
f2py extension, and tests numpy, h5py and numba where present):

```bash
./test_in_container.sh python3.12 snakepit-modern.sif            # preinstalled packages
./test_in_container.sh python3.12 snakepit-modern.sif fresh      # empty venv, install wheels
./test_in_container.sh python3.16 snakepit-modern.sif bare       # stdlib only
```

All images:

```bash
python3 test_images.py
```

The (version, image) pairs are `PYTHON_VERSIONS` in `test_images.py`. Images
for another architecture, or not built, are skipped. It stops at the first
failure and writes `test_results.log`. `SNAKEPIT_TEST_MODE=fresh` installs
wheels into empty venvs instead of using the preinstalled packages.

Last run (2026-11-11): 31/31 on x86_64, 7/7 on POWER9.

## numpy 1 and numpy 2

The numpy C ABI is one-way. An extension built against numpy 2 imports on
numpy 1 and 2. An extension built against numpy 1 fails on numpy 2
(`numpy.core.multiarray failed to import`). Build wheels against numpy 2.

numpy 1 interpreters: `snakepit-legacy.sif` (2.7-3.8), `snakepit-p9.sif`
python3.8 and python3.11, and at ESRF `module load jupyter-slurm` on x86_64:

| jupyter-slurm | Python | numpy | h5py | numba |
|---|---|---|---|---|
| 2022.05.1 | 3.9.12 | 1.21.6 | 3.6.0 | 0.55.1 |
| 2023.10.0-.11 | 3.11.6 | 1.24.4 | 3.10.0 | 0.57.1 |
| 2025.04.1-.6 (latest) | 3.12.9 | 1.26.4 | 3.13.0 | 0.61.0 |

`test_numpy_abi.sh` checks both directions, using jupyter-slurm latest as the
numpy 1 side and `snakepit-modern.sif` python3.12 as the numpy 2 side:

```bash
sbatch test_numpy_abi.sh [NUMPY1_PYTHON]
```

## Rules

- Interpreters and packages come from existing binaries: PyPI wheels, the
  silx wheelhouse, scientific-python nightlies, conda-forge. Compile upstream
  packages only to test a git head that has no nightly.
- Repository files are 7-bit ASCII.
- Test code runs on Python 2.7: no f-strings.
