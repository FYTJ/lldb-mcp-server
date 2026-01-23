#!/bin/bash
# Set up LLDB environment variables for running the server.

export LLDB_PYTHON_PATH="$(/usr/bin/lldb -P)"
export PYTHONPATH="${LLDB_PYTHON_PATH}:${PYTHONPATH}"
export LLDB_MCP_ALLOW_LAUNCH=1
export LLDB_MCP_ALLOW_ATTACH=1

echo "LLDB environment configured:"
echo "  LLDB_PYTHON_PATH=$LLDB_PYTHON_PATH"
echo "  PYTHONPATH=$PYTHONPATH"
