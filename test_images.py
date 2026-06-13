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
TEST_EXT_DIR = SCRIPT_DIR / "test_extension"
EXTENSION_FILES = ["arraysum.c", "arraysum.pyf", "build_extension.sh", "test_uniform.py"]
LOG_FILE = SCRIPT_DIR / "test_results.log"

# Python versions to test
# Format: (version, image, numpy_spec, numba_spec, h5py_spec)
# Note: Python 2.7 installs llvmlite==0.29.0 separately (handled in code)
PYTHON_VERSIONS = [
    ("2.7", "snakepit:u20", "numpy<1.17", "numba==0.45.0", "h5py"),
    ("3.8", "snakepit:u20", "numpy", "numba", "h5py"),
    ("3.9", "snakepit:u24", "numpy", "numba", "h5py"),
    ("3.10", "snakepit:u24", "numpy", "numba", "h5py"),
    ("3.11", "snakepit:u24", "numpy", "numba", "h5py"),
    ("3.12", "snakepit:u24", "numpy", "numba", "h5py"),
    ("3.13", "snakepit:u24", "numpy", "numba", "h5py"),
    ("3.14", "snakepit:u24", "numpy", "numba", "h5py"),
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
    line = "\n" + "="*70
    print("\n" + Colors.BOLD + Colors.BLUE + "="*70 + Colors.RESET)
    print(Colors.BOLD + Colors.BLUE + message + Colors.RESET)
    print(Colors.BOLD + Colors.BLUE + "="*70 + Colors.RESET + "\n")
    log_write(line)
    log_write(message)
    log_write('='*70 + '\n')


def print_success(message):
    """Print a success message."""
    print(Colors.GREEN + "✓ " + message + Colors.RESET)
    log_write("✓ " + message)


def print_error(message):
    """Print an error message."""
    print(Colors.RED + "✗ " + message + Colors.RESET)
    log_write("✗ " + message)


def print_step(message):
    """Print a step message."""
    print(Colors.YELLOW + "→ " + message + Colors.RESET)
    log_write("→ " + message)


def run_docker(image, python_version, command, capture_output=False):
    """Run a command in a Docker container."""
    uid = os.getuid()
    gid = os.getgid()
    
    docker_cmd = [
        "docker", "run", "--rm",
        "--user", str(uid) + ":" + str(gid),
        "-e", "HOME=/workspace",
        "-v", str(WORKSPACE_DIR) + ":/workspace",
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


def test_python_version(python_version, image, numpy_spec, numba_spec, h5py_spec):
    """
    Test a specific Python version with uniform test code.
    
    Steps:
    1. Create virtual environment
    2. Install numpy, numba, h5py in venv
    3. Build C extension with f2py
    4. Run uniform test script (same code for all Python versions)
    """
    print_header("Testing Python " + python_version)
    
    # Clean version string for venv name
    venv_name = "venv_py" + python_version.replace(".", "")
    system_py = "python" + python_version
    venv_py = venv_name + "/bin/python"
    
    # Step 1: Create virtual environment
    print_step("Step 1: Creating virtual environment with " + system_py)
    
    if python_version == "2.7":
        create_cmd = system_py + " -m virtualenv " + venv_name
    else:
        create_cmd = system_py + " -m venv " + venv_name
    
    retcode, stdout, stderr = run_docker(image, python_version, create_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("Failed to create venv")
        log_write("STDOUT:\n" + stdout)
        log_write("STDERR:\n" + stderr)
        print("STDOUT:\n" + stdout)
        print("STDERR:\n" + stderr)
        return False
    
    print_success("Virtual environment created: " + venv_name)
    
    # Step 2: Install packages in venv
    print_step("Step 2: Installing packages in venv")
    
    # For Python 2.7, install llvmlite first due to dependency issues
    if python_version == "2.7":
        llvm_cmd = venv_py + " -m pip install --upgrade pip && " + venv_py + " -m pip install 'llvmlite==0.29.0'"
        retcode, stdout, stderr = run_docker(image, python_version, llvm_cmd, capture_output=True)
        if retcode != 0:
            print_error("Failed to install llvmlite")
            log_write("STDOUT:\n" + stdout)
            log_write("STDERR:\n" + stderr)
            print("STDOUT:\n" + stdout)
            print("STDERR:\n" + stderr)
            return False
        packages = [numpy_spec, h5py_spec, "numba==0.45.0"]
    else:
        packages = [numpy_spec, h5py_spec, numba_spec]
    
    packages_str = " ".join(["'" + p + "'" for p in packages])
    install_cmd = venv_py + " -m pip install " + packages_str
    retcode, stdout, stderr = run_docker(image, python_version, install_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("Failed to install packages")
        log_write("STDOUT:\n" + stdout)
        log_write("STDERR:\n" + stderr)
        print("STDOUT:\n" + stdout)
        print("STDERR:\n" + stderr)
        return False
    
    print_success("Packages installed: " + ", ".join(packages))
    log_write("Installation output:\n" + stdout)
    
    # Step 3: Build C extension with f2py using venv python
    print_step("Step 3: Building C extension with f2py")
    
    build_cmd = "cd /workspace && bash build_extension.sh " + venv_py
    retcode, stdout, stderr = run_docker(image, python_version, build_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("Failed to build C extension")
        log_write("STDOUT:\n" + stdout)
        log_write("STDERR:\n" + stderr)
        print("STDOUT:\n" + stdout)
        print("STDERR:\n" + stderr)
        return False
    
    print_success("C extension built with f2py")
    log_write("Build output:\n" + stdout)
    
    # Step 4: Run uniform test script
    print_step("Step 4: Running uniform test (same code for all Python versions)")
    
    test_cmd = "cd /workspace && " + venv_py + " test_uniform.py"
    retcode, stdout, stderr = run_docker(image, python_version, test_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("Uniform test failed")
        log_write("STDOUT:\n" + stdout)
        log_write("STDERR:\n" + stderr)
        print("STDOUT:\n" + stdout)
        print("STDERR:\n" + stderr)
        return False
    
    print_success("All tests passed")
    print("  Output:\n    " + stdout.strip().replace("\n", "\n    "))
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
        print_header("Snakepit Docker Image Test Suite")
        print("Logging to: " + str(LOG_FILE))
        log_write("Logging to: " + str(LOG_FILE) + "\n")
        
        # Prepare workspace
        prepare_workspace()
        
        # Run tests
        results = {}
        for python_version, image, numpy_spec, numba_spec, h5py_spec in PYTHON_VERSIONS:
            success = test_python_version(python_version, image, numpy_spec, numba_spec, h5py_spec)
            results[python_version] = success
            
            if not success:
                print_error("Python " + python_version + " test FAILED")
                log_write("Python " + python_version + " test FAILED")
                print("\nStopping tests to fix this issue first.")
                print("\nTo debug, you can run:")
                print("  docker run --rm -it --user $(id -u):$(id -g) -e HOME=/workspace \\")
                print("    -v " + str(WORKSPACE_DIR) + ":/workspace -w /workspace " + image + " bash")
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
        print("\n" + Colors.BOLD + summary + Colors.RESET)
        log_write(summary)
        log_write("\nLog file: " + str(LOG_FILE))
        
        return 0 if passed == total else 1
    
    finally:
        if _log_file:
            _log_file.close()


if __name__ == "__main__":
    sys.exit(main())
