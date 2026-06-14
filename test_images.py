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
PYTHON_VERSIONS = [
    ("2.7", "ubuntu20.04.sif"),
    ("3.8", "ubuntu20.04.sif"),
    ("3.9", "ubuntu24.04.sif"),
    ("3.10", "ubuntu24.04.sif"),
    ("3.11", "ubuntu24.04.sif"),
    ("3.12", "ubuntu24.04.sif"),
    ("3.13", "ubuntu24.04.sif"),
    ("3.14", "ubuntu24.04.sif"),
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
    print(Colors.GREEN + "[OK] " + message + Colors.RESET)
    log_write("[OK] " + message)


def print_error(message):
    """Print an error message."""
    print(Colors.RED + "[FAIL] " + message + Colors.RESET)
    log_write("[FAIL] " + message)


def print_step(message):
    """Print a step message."""
    print(Colors.YELLOW + ">> " + message + Colors.RESET)
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
        print("\n" + Colors.BOLD + summary + Colors.RESET)
        log_write(summary)
        log_write("\nLog file: " + str(LOG_FILE))
        
        return 0 if passed == total else 1
    
    finally:
        if _log_file:
            _log_file.close()


if __name__ == "__main__":
    sys.exit(main())
