#!/usr/bin/env python3
"""
Test script for snakepit Docker images.
Tests that each Python version can create venvs, install numpy, and build C extensions.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

# Test configuration
SCRIPT_DIR = Path(__file__).parent.absolute()
WORKSPACE_DIR = SCRIPT_DIR / "test_workspace"
TEST_EXT_DIR = SCRIPT_DIR.parent / "test_extension"
EXTENSION_FILES = ["arraysum.c", "arraysum.pyf", "build_extension.sh"]

# Python versions to test
PYTHON_VERSIONS = [
    ("2.7", "snakepit:u20", "numpy<1.17"),
    ("3.8", "snakepit:u20", "numpy"),
    ("3.9", "snakepit:u24", "numpy"),
    ("3.10", "snakepit:u24", "numpy"),
    ("3.11", "snakepit:u24", "numpy"),
    ("3.12", "snakepit:u24", "numpy"),
    ("3.13", "snakepit:u24", "numpy"),
    ("3.14", "snakepit:u24", "numpy"),
]


class Colors:
    """ANSI color codes for output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_step(message):
    """Print a step message."""
    print(f"{Colors.YELLOW}→ {message}{Colors.RESET}")


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


def test_python_version(python_version, image, numpy_version):
    """
    Test a specific Python version.
    
    Steps:
    1. Create virtual environment
    2. Install numpy in venv
    3. Build C extension with venv python
    4. Test C extension with venv python
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
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success(f"Virtual environment created: {venv_name}")
    
    # Step 2: Install numpy in venv
    print_step(f"Step 2: Installing numpy in venv")
    
    install_cmd = f"{venv_py} -m pip install --upgrade pip && {venv_py} -m pip install '{numpy_version}'"
    retcode, stdout, stderr = run_docker(image, python_version, install_cmd, capture_output=True)
    
    if retcode != 0:
        print_error(f"Failed to install numpy")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success("numpy installed")
    
    # Step 3: Build C extension with f2py using venv python
    print_step("Step 3: Building C extension with f2py")
    
    build_cmd = f"cd /workspace && bash build_extension.sh {venv_py}"
    retcode, stdout, stderr = run_docker(image, python_version, build_cmd, capture_output=True)
    
    if retcode != 0:
        print_error("Failed to build C extension")
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success("C extension built with f2py")
    
    # Step 4: Test C extension with venv python
    print_step("Step 4: Testing C extension")
    
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
        print(f"STDOUT:\n{stdout}")
        print(f"STDERR:\n{stderr}")
        return False
    
    print_success("C extension test passed")
    print(f"  Output: {stdout.strip()}")
    
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
    print_header("Snakepit Docker Image Test Suite")
    
    # Prepare workspace
    prepare_workspace()
    
    # Run tests
    results = {}
    for python_version, image, numpy_version in PYTHON_VERSIONS:
        success = test_python_version(python_version, image, numpy_version)
        results[python_version] = success
        
        if not success:
            print_error(f"Python {python_version} test FAILED")
            print("\nStopping tests to fix this issue first.")
            print(f"\nTo debug, you can run:")
            print(f"  docker run --rm -it --user $(id -u):$(id -g) -e HOME=/workspace \\")
            print(f"    -v {WORKSPACE_DIR}:/workspace -w /workspace {image} bash")
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
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} passed{Colors.RESET}\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
