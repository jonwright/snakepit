#!/usr/bin/env python3
"""
Test script for snakepit Apptainer images.
Tests that each Python version can create venvs, install numpy/numba/h5py, and build C extensions.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Test configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
WORKSPACE_DIR = SCRIPT_DIR / "test_workspace"
TEST_EXT_DIR = SCRIPT_DIR / "test_extension"
EXTENSION_FILES = ["arraysum.c", "arraysum.pyf", "build_extension.sh", "test_uniform.py", "run_tests.sh", "requirements.txt"]
LOG_FILE = SCRIPT_DIR / "test_results.log"

# Python versions to test
# Format: (version, sif_file)
#
# Three-container layout (consolidated from six -- see AGENTS.md):
#   snakepit-legacy.sif       Ubuntu 18.04: 2.7, 3.6, 3.7 (native apt) + 3.8 (uv prebuilt)
#                    + PyPy 2.7 (pypy.org tarball), PyPy 3.9 (uv prebuilt)
#   snakepit-manylinux2014.sif  CentOS 7 (glibc 2.17), pypa-maintained: 3.9-3.11 tested here;
#                    3.12+/3.14t/3.15/3.15t interpreters exist but numpy has no
#                    manylinux2014 wheels for them and the image's GCC 10.2 can't
#                    build numpy from source, so those are NOT in this test matrix.
#   snakepit-modern.sif       Ubuntu 24.04 (apt + deadsnakes + uv): 3.12-3.15, 3.14t/3.15t --
#                    modern glibc means real numpy/h5py/numba wheels install cleanly.
PYTHON_VERSIONS = [
    ("2.7", "snakepit-legacy.sif"),
    ("3.6", "snakepit-legacy.sif"),
    ("3.7", "snakepit-legacy.sif"),
    ("3.8", "snakepit-legacy.sif"),
    ("3.9", "snakepit-manylinux2014.sif"),
    ("3.10", "snakepit-manylinux2014.sif"),
    ("3.11", "snakepit-manylinux2014.sif"),
    ("3.12", "snakepit-modern.sif"),
    ("3.13", "snakepit-modern.sif"),
    ("3.14", "snakepit-modern.sif"),
    ("3.14t", "snakepit-modern.sif"),
    ("3.15", "snakepit-modern.sif"),
    ("3.15t", "snakepit-modern.sif"),
    # Cross-architecture containers (QEMU user-mode emulation required for build/test)
    ("3.11", "ubuntu20.04_ppc64le.sif"),
    ("3.11", "ubuntu24.04_aarch64.sif"),
    # PyPy containers (cpython-compatible cpyext ABI testing)
    ("pypy2.7", "snakepit-legacy.sif"),
    ("pypy3.9", "snakepit-legacy.sif"),
    ("pypy3.11", "snakepit-manylinux2014.sif"),
]





# Global log file handle
_log_file = None


def log_write(message):
    """Write a message to the log file."""
    if _log_file:
        _log_file.write(message + '\n')
        _log_file.flush()


def print_header(message):
    """Print a formatted header."""
    line = "\n" + "="*70
    print("\n" + "="*70)
    print(message)
    print("="*70 + "\n")
    log_write(line)
    log_write(message)
    log_write('='*70 + '\n')


def print_success(message):
    """Print a success message."""
    print("[OK] " + message)
    log_write("[OK] " + message)


def print_error(message):
    """Print an error message."""
    print("[FAIL] " + message)
    log_write("[FAIL] " + message)


def print_step(message):
    """Print a step message."""
    print(">> " + message)
    log_write(">> " + message)


def run_apptainer(sif_file, python_version, command, capture_output=False):
    """Run a command in an Apptainer container."""
    sif_path = SCRIPT_DIR / sif_file
    
    apptainer_cmd = [
        "apptainer", "exec",
        "-e",
        "-B", str(WORKSPACE_DIR) + ":/workspace",
        "--pwd", "/workspace",
        str(sif_path),
        "/bin/bash", "-c", command
    ]
    
    try:
        if capture_output:
            result = subprocess.run(
                apptainer_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(apptainer_cmd, timeout=300)
            return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        print_error("Command timed out after 300 seconds")
        return 1, "", ""
    except Exception as e:
        print_error("Error running apptainer: " + str(e))
        return 1, "", ""


def test_python_version(python_version, sif_file):
    """
    Test a specific Python version.
    
    Runs a single Apptainer command that:
    1. Creates virtual environment
    2. Installs packages from requirements.txt (handles version dependencies)
    3. Builds C extension with f2py
    4. Runs uniform test script
    """
    print_header("Testing Python " + python_version)
    
    if python_version.startswith("python") or python_version.startswith("pypy"):
        system_py = python_version
    else:
        system_py = "python" + python_version
    
    # Single command to run all tests
    print_step("Running unified test with " + system_py)
    
    test_cmd = "cd /workspace && bash run_tests.sh " + system_py
    retcode, stdout, stderr = run_apptainer(sif_file, python_version, test_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("Test failed")
        log_write("STDOUT:\n" + stdout)
        log_write("STDERR:\n" + stderr)
        print("STDOUT:\n" + stdout)
        print("STDERR:\n" + stderr)
        return False
    
    print_success("All tests passed")
    print("\n" + stdout.strip())
    log_write("Test output:\n" + stdout)
    
    return True


def prepare_workspace():
    """Prepare the test workspace."""
    print_step("Preparing test workspace...")
    
    # Clean workspace
    if WORKSPACE_DIR.exists():
        shutil.rmtree(WORKSPACE_DIR)
    WORKSPACE_DIR.mkdir()
    
    # Copy extension files to workspace
    for filename in EXTENSION_FILES:
        src = TEST_EXT_DIR / filename
        dst = WORKSPACE_DIR / filename
        if not src.exists():
            print_error(f"Source file not found: {src}")
            sys.exit(1)
        shutil.copy(src, dst)
        # Make build script executable
        if filename.endswith('.sh'):
            os.chmod(dst, 0o755)
    
    print_success("Workspace prepared")


def main():
    """Main test runner."""
    global _log_file
    
    # Open log file
    _log_file = open(LOG_FILE, 'w')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_write("Snakepit Test Suite - " + timestamp + "\n")
    
    try:
        print_header("Snakepit Apptainer Image Test Suite")
        print("Logging to: " + str(LOG_FILE))
        log_write("Logging to: " + str(LOG_FILE) + "\n")
        
        # Prepare workspace
        prepare_workspace()
        
        # Run tests
        results = {}
        for python_version, sif_file in PYTHON_VERSIONS:
            success = test_python_version(python_version, sif_file)
            results[python_version] = success
            
            if not success:
                print_error("Python " + python_version + " test FAILED")
                log_write("Python " + python_version + " test FAILED")
                print("\nStopping tests to fix this issue first.")
                print("\nTo debug, you can run:")
                sif_path = SCRIPT_DIR / sif_file
                print("  apptainer shell -e -B " + str(WORKSPACE_DIR) + ":/workspace " + str(sif_path))
                log_write("\nStopping tests to fix this issue first.")
                return 1
        
        # Print summary
        print_header("Test Summary")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for version, success in results.items():
            if success:
                print_success("Python " + version)
            else:
                print_error("Python " + version)
        
        summary = "\nResults: " + str(passed) + "/" + str(total) + " passed\n"
        print(summary)
        log_write(summary)
        log_write("\nLog file: " + str(LOG_FILE))
        
        return 0 if passed == total else 1
    
    finally:
        if _log_file:
            _log_file.close()


if __name__ == "__main__":
    sys.exit(main())
