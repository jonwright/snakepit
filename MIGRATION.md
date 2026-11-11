# Migration Guide: Six Containers to Three

Snakepit's container layout was consolidated from six images to three. This
guide is for anyone with scripts, job files, or muscle memory built around
the old names.

## Filename map

| Old file (retired) | Old `.sif` | New file | New `.sif` |
|---|---|---|---|
| `ubuntu20.04.def` | `ubuntu20.04.sif` | `snakepit-legacy.def` | `snakepit-legacy.sif` |
| `debian10.def` | `debian10.sif` | `snakepit-legacy.def` | `snakepit-legacy.sif` |
| `ubuntu24.04.def` | `ubuntu24.04.sif` | `snakepit-modern.def` | `snakepit-modern.sif` |
| `ubuntu26.04.def` | `ubuntu26.04.sif` | `snakepit-modern.def` | `snakepit-modern.sif` |
| `ubuntu24.04_pypy.def` | `ubuntu24.04_pypy.sif` | split across `snakepit-legacy.def` and `snakepit-manylinux2014.def` | `snakepit-legacy.sif` / `snakepit-manylinux2014.sif` |
| `manylinux2014.def` | `manylinux2014.sif` | `snakepit-manylinux2014.def` (renamed only) | `snakepit-manylinux2014.sif` |

`ubuntu20.04_ppc64le.def` was removed and replaced by `snakepit-p9.def` +
`build_p9.sh` (native POWER9 image, `snakepit-p9.sif` -- see README/AGENTS).
`ubuntu24.04_aarch64.def` is **unchanged** -- still a separate Python 3.11 QEMU
smoke test, not touched by this consolidation.

## Python version -> new container map

| Version | Old container(s) | New container |
|---|---|---|
| 2.7 | `ubuntu20.04.sif` | `snakepit-legacy.sif` |
| 3.6 | `debian10.sif` | `snakepit-legacy.sif` |
| 3.7 | `ubuntu24.04.sif` | `snakepit-legacy.sif` |
| 3.8 | `ubuntu20.04.sif` | `snakepit-legacy.sif` |
| 3.9 | `ubuntu24.04.sif` **and** `manylinux2014.sif` | `snakepit-modern.sif` **and** `snakepit-manylinux2014.sif` |
| 3.10 | `ubuntu24.04.sif` **and** `manylinux2014.sif` | `snakepit-modern.sif` **and** `snakepit-manylinux2014.sif` |
| 3.11 | `ubuntu24.04.sif` **and** `manylinux2014.sif` | `snakepit-modern.sif` **and** `snakepit-manylinux2014.sif` |
| 3.12 | `ubuntu24.04.sif` **and** `manylinux2014.sif`\* | `snakepit-modern.sif` |
| 3.13 | `ubuntu24.04.sif` **and** `manylinux2014.sif`\* | `snakepit-modern.sif` |
| 3.14 | `ubuntu24.04.sif` **and** `manylinux2014.sif`\* | `snakepit-modern.sif` |
| 3.14t | `ubuntu24.04.sif` | `snakepit-modern.sif` |
| 3.15 | `ubuntu26.04.sif` | `snakepit-modern.sif` |
| 3.15t | `ubuntu26.04.sif` | `snakepit-modern.sif` |
| PyPy 2.7 | `ubuntu24.04_pypy.sif` | `snakepit-legacy.sif` |
| PyPy 3.9 | `ubuntu24.04_pypy.sif` | `snakepit-legacy.sif` |
| PyPy 3.11 | `ubuntu24.04_pypy.sif` | `snakepit-modern.sif` |

\* The old `manylinux2014.sif` listed 3.12-3.14 as covered, but numpy's
wheels for that old glibc/GCC baseline thin out above cp311 (numpy 2.2.6
still covers cp312/cp313; cp314+ has none) -- those specific
(version, old-glibc) checks were already silently broken before this
consolidation, independent of it. `snakepit-modern.sif` is where 3.12-3.14
get real testing now; the old-glibc leg for them is gone because it no
longer worked, not because of anything this migration removed.

3.9/3.10/3.11 keep their original dual-glibc testing intentionally: they run
in **both** `snakepit-modern.sif` (modern glibc) and
`snakepit-manylinux2014.sif` (old glibc), exactly as the old six-container
design tested them in both `ubuntu24.04.sif` and `manylinux2014.sif`.

## What to change in your scripts

Anywhere you have:

```bash
apptainer build --fakeroot ubuntu20.04.sif ubuntu20.04.def
apptainer build --fakeroot debian10.sif debian10.def
apptainer build --fakeroot ubuntu24.04.sif ubuntu24.04.def
apptainer build --fakeroot ubuntu26.04.sif ubuntu26.04.def
apptainer build --fakeroot manylinux2014.sif manylinux2014.def
apptainer build --fakeroot ubuntu24.04_pypy.sif ubuntu24.04_pypy.def
```

replace it with:

```bash
apptainer build --fakeroot snakepit-legacy.sif snakepit-legacy.def
apptainer build --fakeroot snakepit-manylinux2014.sif snakepit-manylinux2014.def
apptainer build --fakeroot snakepit-modern.sif snakepit-modern.def
```

Anywhere a job script or `test_in_container.sh` call names an old `.sif`
file, swap in the new container from the version map above, e.g.:

```bash
# Old
./test_in_container.sh python2.7 ubuntu20.04.sif
./test_in_container.sh python3.6 debian10.sif
./test_in_container.sh pypy3.11 ubuntu24.04_pypy.sif

# New
./test_in_container.sh python2.7 snakepit-legacy.sif
./test_in_container.sh python3.6 snakepit-legacy.sif
./test_in_container.sh pypy3.11 snakepit-modern.sif
```

If you have HPC module files or job scripts that hardcode a path like
`/apps/snakepit/ubuntu24.04.sif`, update them to point at the new filename
(`/apps/snakepit/snakepit-modern.sif`) -- the old `.sif` files still work
fine standalone if you have them already built, this is purely a naming
change plus the container reshuffle in the table above.

## Behavioral changes worth knowing about

- **3.6** now comes from a native Ubuntu 18.04 apt package instead of the
  official `python:3.6.15-buster` Docker image. Same CPython 3.6.15, just a
  different (and simpler) binary source.
- **3.8** now comes from `uv`/python-build-standalone instead of Ubuntu
  20.04's own apt package, since no distro or PPA ships 3.8 anymore.
- **PyPy 3.11** now comes `uv`-installed into `snakepit-modern.sif` (pinned
  to pypy-3.11.15 = PyPy 7.3.23) instead of the upstream `manylinux2014`
  image, because numpy's pp311 wheels need glibc >= 2.28 (CentOS 7 is 2.17).
- If you were relying on `ubuntu20.04.sif`/`debian10.sif`'s specific base OS
  (e.g. testing against Ubuntu 20.04's or Debian 10's particular glibc/libc
  versions for reasons unrelated to Python version), note the replacement
  base for 2.7/3.6/3.7/3.8 is now Ubuntu 18.04 throughout, not a mix of
  Ubuntu 20.04 and Debian 10.

## Not yet migrated

The cross-architecture images are no longer both narrow QEMU smoke tests:
`snakepit-p9.sif` now covers ppc64le **natively** (Python 3.8, 3.11-3.15, 3.14t, via
`snakepit-p9.def` + `build_p9.sh`), replacing the older
`ubuntu20.04_ppc64le.def` QEMU single-Python-3.11 image. aarch64 remains a
narrow single-Python-3.11 QEMU smoke test (`ubuntu24.04_aarch64.def`).
Building full `snakepit-legacy`/`snakepit-manylinux2014`/
`snakepit-manylinux_2_28`/`snakepit-modern` equivalents for aarch64
(with the same version matrix) is planned but not started -- see the
"Multi-architecture note" in `README.md`.
