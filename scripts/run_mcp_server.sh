#!/usr/bin/env bash
set -euo pipefail
HOST="${MCP_HOST:-127.0.0.1}"
PORT="${MCP_PORT:-8765}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_PATH="$(cd "$SCRIPT_DIR/.." && pwd)/src"
PYV="$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYPATH=""
if command -v lldb >/dev/null 2>&1; then
  PYPATH="$(lldb -P || true)"
fi
if [ -z "$PYPATH" ] && [ -d "/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python" ]; then
  PYPATH="/Applications/Xcode.app/Contents/SharedFrameworks/LLDB.framework/Resources/Python"
fi
if [ -z "$PYPATH" ] && [ -d "/Library/Developer/CommandLineTools/Library/PrivateFrameworks/LLDB.framework/Resources/Python" ]; then
  PYPATH="/Library/Developer/CommandLineTools/Library/PrivateFrameworks/LLDB.framework/Resources/Python"
fi
BREW_LLVM=""
if command -v brew >/dev/null 2>&1; then
  BREW_LLVM="$(brew --prefix llvm || true)"
fi
if [ -z "$PYPATH" ] && [ -n "$BREW_LLVM" ] && [ -d "$BREW_LLVM/lib/python$PYV/site-packages" ]; then
  PYPATH="$BREW_LLVM/lib/python$PYV/site-packages"
fi
export PYTHONPATH="$SRC_PATH${PYTHONPATH:+:$PYTHONPATH}"
if [ -n "$PYPATH" ]; then
  export PYTHONPATH="$PYPATH:$PYTHONPATH"
fi
FWPATH=""
if [ -d "/Applications/Xcode.app/Contents/SharedFrameworks" ]; then
  FWPATH="/Applications/Xcode.app/Contents/SharedFrameworks"
fi
if [ -z "$FWPATH" ] && [ -d "/Library/Developer/CommandLineTools/Library/PrivateFrameworks" ]; then
  FWPATH="/Library/Developer/CommandLineTools/Library/PrivateFrameworks"
fi
if [ -z "$FWPATH" ] && [ -n "$BREW_LLVM" ] && [ -d "$BREW_LLVM/lib" ]; then
  export DYLD_LIBRARY_PATH="$BREW_LLVM/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi
if [ -n "$FWPATH" ]; then
  export DYLD_FRAMEWORK_PATH="$FWPATH${DYLD_FRAMEWORK_PATH:+:$DYLD_FRAMEWORK_PATH}"
  export DYLD_LIBRARY_PATH="$FWPATH${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi
export PYTHONUNBUFFERED=1
export LLDB_MCP_ALLOW_LAUNCH="${LLDB_MCP_ALLOW_LAUNCH:-1}"
PYEXEC="/Applications/Xcode.app/Contents/Developer/usr/bin/python3"
if [ ! -x "$PYEXEC" ]; then
  PYEXEC="python3"
fi
"$PYEXEC" -u -m lldb_mcp_server.mcp.server --listen "$HOST:$PORT"
