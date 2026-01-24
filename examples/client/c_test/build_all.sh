#!/bin/bash
# Build all test programs with debug symbols
# Usage: ./build_all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building test programs in: $SCRIPT_DIR"
echo "---"

for dir in */; do
    name="${dir%/}"
    if [ -f "${dir}${name}.c" ]; then
        echo "Building ${name}..."
        cc -g -O0 -Wall -Wextra -Wno-format-security -o "${dir}${name}" "${dir}${name}.c"
        dsymutil "${dir}${name}" 2>/dev/null || true
        echo "  -> ${dir}${name}"
    fi
done

echo "---"
echo "All test programs built successfully."
echo ""
echo "Available test binaries:"
for dir in */; do
    name="${dir%/}"
    if [ -x "${dir}${name}" ]; then
        echo "  - ${dir}${name}"
    fi
done
