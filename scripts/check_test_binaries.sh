#!/bin/bash
# Check that all test binaries exist and are executable

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_DIR="$PROJECT_ROOT/examples/client/c_test"

echo "Checking test binaries in: $TEST_DIR"
echo ""

# List of expected test programs
TEST_PROGRAMS=(
    "null_deref/null_deref"
    "buffer_overflow/buffer_overflow"
    "use_after_free/use_after_free"
    "infinite_loop/infinite_loop"
    "divide_by_zero/divide_by_zero"
    "stack_overflow/stack_overflow"
    "format_string/format_string"
    "double_free/double_free"
)

MISSING_COUNT=0
TOTAL_COUNT=${#TEST_PROGRAMS[@]}

for prog in "${TEST_PROGRAMS[@]}"; do
    FULL_PATH="$TEST_DIR/$prog"

    if [ -f "$FULL_PATH" ] && [ -x "$FULL_PATH" ]; then
        echo "✅ $prog"
    else
        echo "❌ $prog - MISSING OR NOT EXECUTABLE"
        MISSING_COUNT=$((MISSING_COUNT + 1))
    fi
done

echo ""
echo "---"
if [ $MISSING_COUNT -eq 0 ]; then
    echo "✅ All $TOTAL_COUNT test binaries are ready"
    exit 0
else
    echo "❌ $MISSING_COUNT/$TOTAL_COUNT test binaries are missing"
    echo ""
    echo "Run the following to build all test programs:"
    echo "  cd $TEST_DIR && ./build_all.sh"
    exit 1
fi
