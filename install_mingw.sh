#!/bin/bash
# Install MinGW-w64 cross-compiler for c2py23 Windows port
# Run as: sudo bash install_mingw.sh

set -e

echo "=== Installing MinGW-w64 cross-compiler ==="

apt-get update -qq
apt-get install -y -qq gcc-mingw-w64-x86-64

echo ""
echo "=== Done ==="
echo "Verifying:"
x86_64-w64-mingw32-gcc --version
which x86_64-w64-mingw32-gcc
