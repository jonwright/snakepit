#!/usr/bin/env python3
"""
Test script for snakepit Docker images.
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
TEST_EXT_DIR = SCRIPT_DIR.parent / "test_extension"
EXTENSION_FILES = ["arraysum.c", "arraysum.pyf", "build_extension.sh"]
LOG_FILE = SCRIPT_DIR / "test_results.log"

# Python versions to test
# Format: (version, image, numpy_spec, has_numba, has_h5py)
PYTHON_VERSIONS = [
    ("2.7", "snakepit:u20", "numpy<1.17", False, True),    # numba doesn't support 2.7
    ("3.8", "snakepit:u20", "numpy", True, True),
    ("3.9", "snakepit:u24", "numpy", True, True),
    ("3.10", "snakepit:u24", "numpy", True, True),
    ("3.11", "snakepit:u24", "numpy", True, True),
    ("3.12", "snakepit:u24", "numpy", True, True),
    ("3.13", "snakepit:u24", "numpy", True, True),
    ("3.14", "snakepit:u24", "numpy", True, True),
]


class Colors:
    """ANSI color codes for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


# Global log file handle
_log_file = None


def log_write(message, strip_colors=True):
    """Write a message to the log file."""
    if _log_file:
        if strip_colors:
            # Strip ANSI color codes
            import re
            message = re.sub(r'\033\[[0-9;]+m', '', message)
        _log_file.write(message + '\n')
        _log_file.flush()


def print_header(message):
    """Print a formatted header."""
    line = f"\n{'='*70}"
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    log_write(line)
    log_write(message)
    log_write('='*70 + '\n')


def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    log_write(f"✓ {message}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    log_write(f"✗ {message}")


def print_step(message):
    """Print a step message."""
    print(f"{Colors.YELLOW}→ {message}{Colors.RESET}")
    log_write(f"→ {message}")


def run_docker(image, python_version, command, capture_output=False):
    """Run a command in a Docker container."""
    uid = os.getuid()
    gid = os.getgid()
    
    docker_cmd = [
        "docker", "run", "--rm",
        "--user", f"{uid}:{gid}",
        "-e", "HOME=/workspace",
        "-v", f"{WORKSPACE_DIR}:/workspace",
        "-w", "/workspace",
        image,
        "bash", "-c", command
    ]
    
    try:
        if capture_output:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(docker_cmd, timeout=300)
            return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out after 300 seconds")
        return 1, "", ""
    except Exception as e:
        print_error(f"Error running docker: {e}")
        return 1, "", ""


def test_python_version(python_version, image, numpy_version, has_numba, has_h5py):
    """
    Test a specific Python version.
    
    Steps:
    1. Create virtual environment
    2. Install numpy, numba (if supported), h5py in venv
    3. Test numba and h5py
    4. Build C extension with venv python
    5. Test C extension with venv python
    """
    print_header(f"Testing Python {python_version}")
    
    # Clean version string for venv name
    venv_name = f"venv_py{python_version.replace('.', '')}"
    system_py = f"python{python_version}"
    venv_py = f"{venv_name}/bin/python"
    
    # Step 1: Create virtual environment
    print_step(f"Step 1: Creating virtual environment with {system_py}")
    
    if python_version == "2.7":
        create_cmd = f"{system_py} -m virtualenv {venv_name}"
    else:
        create_cmd = f"{system_py} -m venv {venv_name}"
    
    retcode, stdout, stderr = run_docker(image, python_version, create_cmd, capture_output=True)
    
    if retcode != 0:
        print_error(f"Failed to create venv")
        log_write(f"STDOUT:\n{stdout}")
        log_write(f"STDERR:\n{stderr}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success(f"Virtual environment created: {venv_name}")
    
    # Step 2: Install packages in venv
    print_step(f"Step 2: Installing packages in venv")
    
    packages = [numpy_version]
    if has_h5py:
        packages.append("h5py")
    if has_numba:
        packages.append("numba")
    
    packages_str = " ".join([f"'{p}'" for p in packages])
    install_cmd = f"{venv_py} -m pip install --upgrade pip && {venv_py} -m pip install {packages_str}"
    retcode, stdout, stderr = run_docker(image, python_version, install_cmd, capture_output=True)
    
    if retcode != 0:
        print_error(f"Failed to install packages")
        log_write(f"STDOUT:\n{stdout}")
        log_write(f"STDERR:\n{stderr}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success(f"Packages installed: {', '.join(packages)}")
    log_write(f"Installation output:\n{stdout}")
    
    # Step 3: Test h5py
    if has_h5py:
        print_step("Step 3a: Testing h5py")
        h5py_test = f"""cd /workspace && {venv_py} -c '
import h5py
import numpy as np
import tempfile
import os

# Create temporary h5 file
with tempfile.NamedTemporaryFile(delete=False, suffix=".h5") as tf:
    fname = tf.name

try:
    # Write data
    with h5py.File(fname, "w") as f:
        f.create_dataset("test", data=np.array([1, 2, 3, 4, 5]))
    
    # Read data
    with h5py.File(fname, "r") as f:
        data = f["test"][:]
        assert list(data) == [1, 2, 3, 4, 5]
    
    print("h5py test passed: write/read HDF5 file successful")
finally:
    os.unlink(fname)
'"""
        retcode, stdout, stderr = run_docker(image, python_version, h5py_test, capture_output=True)
        
        if retcode != 0:
            print_error("h5py test failed")
            log_write(f"STDOUT:\n{stdout}")
            log_write(f"STDERR:\n{stderr}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return False
        
        print_success("h5py test passed")
        print(f"  Output: {stdout.strip()}")
        log_write(f"h5py test output: {stdout.strip()}")
    
    # Step 4: Test numba
    if has_numba:
        print_step("Step 3b: Testing numba")
        numba_test = f"""cd /workspace && {venv_py} -c '
import numba
import numpy as np

@numba.jit(nopython=True)
def sum_array(arr):
    total = 0.0
    for i in range(len(arr)):
        total += arr[i]
    return total

arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
result = sum_array(arr)
assert abs(result - 15.0) < 1e-10
print("numba test passed: JIT compilation and execution successful")
'"""
        retcode, stdout, stderr = run_docker(image, python_version, numba_test, capture_output=True)
        
        if retcode != 0:
            print_error("numba test failed")
            log_write(f"STDOUT:\n{stdout}")
            log_write(f"STDERR:\n{stderr}")
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            return False
        
        print_success("numba test passed")
        print(f"  Output: {stdout.strip()}")
        log_write(f"numba test output: {stdout.strip()}")
    
    # Step 5: Build C extension with f2py using venv python
    print_step("Step 4: Building C extension with f2py")
    
    build_cmd = f"cd /workspace && bash build_extension.sh {venv_py}"
    retcode, stdout, stderr = run_docker(image, python_version, build_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("Failed to build C extension")
        log_write(f"STDOUT:\n{stdout}")
        log_write(f"STDERR:\n{stderr}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success("C extension built with f2py")
    log_write(f"Build output:\n{stdout}")
    
    # Step 6: Test C extension with venv python
    print_step("Step 5: Testing C extension")
    
    test_cmd = f"""cd /workspace && {venv_py} -c 'import numpy as np
import arraysum
a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, 5.0, 6.0])
result = arraysum.array_sum(a, b)
expected = np.array([5.0, 7.0, 9.0])
assert np.allclose(result, expected)
print("Test passed: [1,2,3] + [4,5,6] = [5,7,9]")
'"""
    
    retcode, stdout, stderr = run_docker(image, python_version, test_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("C extension test failed")
        log_write(f"STDOUT:\n{stdout}")
        log_write(f"STDERR:\n{stderr}")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success("C extension test passed")
    print(f"  Output: {stdout.strip()}")
    log_write(f"Extension test output: {stdout.strip()}")
    
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
    log_write(f"Snakepit Test Suite - {timestamp}\n")
    
    try:
        print_header("Snakepit Docker Image Test Suite")
        print(f"Logging to: {LOG_FILE}")
        log_write(f"Logging to: {LOG_FILE}\n")
        
        # Prepare workspace
        prepare_workspace()
        
        # Run tests
        results = {}
        for python_version, image, numpy_version, has_numba, has_h5py in PYTHON_VERSIONS:
            success = test_python_version(python_version, image, numpy_version, has_numba, has_h5py)
            results[python_version] = success
            
            if not success:
                print_error(f"Python {python_version} test FAILED")
                log_write(f"Python {python_version} test FAILED")
                print("\nStopping tests to fix this issue first.")
                print(f"\nTo debug, you can run:")
                print(f"  docker run --rm -it --user $(id -u):$(id -g) -e HOME=/workspace \\")
                print(f"    -v {WORKSPACE_DIR}:/workspace -w /workspace {image} bash")
                log_write("\nStopping tests to fix this issue first.")
                return 1
        
        # Print summary
        print_header("Test Summary")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for version, success in results.items():
            if success:
                print_success(f"Python {version}")
            else:
                print_error(f"Python {version}")
        
        summary = f"\nResults: {passed}/{total} passed\n"
        print(f"\n{Colors.BOLD}{summary}{Colors.RESET}")
        log_write(summary)
        log_write(f"\nLog file: {LOG_FILE}")
        
        return 0 if passed == total else 1
    
    finally:
        if _log_file:
            _log_file.close()


if __name__ == "__main__":
    sys.exit(main())
