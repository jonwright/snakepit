#!/usr/bin/env python
"""
Uniform test code for all Python versions (2.7 - 3.14).
Tests h5py, numba, and C extension (arraysum).
"""
from __future__ import print_function
import sys
import os
import tempfile
import numpy as np
import h5py
import numba

print("Python version: " + sys.version)

# Test 1: h5py
print("\n=== Testing h5py ===")
try:
    # Create temporary h5 file
    fd, fname = tempfile.mkstemp(suffix=".h5")
    os.close(fd)
    
    # Write data
    with h5py.File(fname, "w") as f:
        f.create_dataset("test", data=np.array([1, 2, 3, 4, 5]))
    
    # Read data
    with h5py.File(fname, "r") as f:
        data = f["test"][:]
        assert list(data) == [1, 2, 3, 4, 5]
    
    print("h5py test PASSED: write/read HDF5 file successful")
finally:
    if os.path.exists(fname):
        os.unlink(fname)

# Test 2: numba
print("\n=== Testing numba ===")

@numba.jit(nopython=True)
def sum_array(arr):
    total = 0.0
    for i in range(len(arr)):
        total += arr[i]
    return total

arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
result = sum_array(arr)
assert abs(result - 15.0) < 1e-10
print("numba test PASSED: JIT compilation and execution successful")

# Test 3: C extension (arraysum)
print("\n=== Testing C extension (arraysum) ===")
import arraysum

a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, 5.0, 6.0])
result = arraysum.array_sum(a, b)
expected = np.array([5.0, 7.0, 9.0])
assert np.allclose(result, expected)
print("C extension test PASSED: [1,2,3] + [4,5,6] = [5,7,9]")

print("\n=== All tests PASSED ===")
