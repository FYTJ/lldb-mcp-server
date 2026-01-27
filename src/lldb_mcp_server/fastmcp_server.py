import importlib
import os
import subprocess
import sys
from pathlib import Path

from fastmcp import FastMCP

from .session.manager import SessionManager
from .tools import (
    register_advanced_tools,
    register_breakpoint_tools,
    register_execution_tools,
    register_inspection_tools,
    register_memory_tools,
    register_security_tools,
    register_session_tools,
    register_target_tools,
    register_watchpoint_tools,
)
from .utils.config import config
from .utils.logging import get_logger

logger = get_logger("lldb.fastmcp")

mcp = FastMCP(
    name="LLDB MCP Server",
    version="0.2.0",
    instructions="A local debugging MCP server based on LLDB",
)

manager = SessionManager()

register_session_tools(mcp, manager)
register_target_tools(mcp, manager)
register_breakpoint_tools(mcp, manager)
register_execution_tools(mcp, manager)
register_inspection_tools(mcp, manager)
register_memory_tools(mcp, manager)
register_watchpoint_tools(mcp, manager)
register_advanced_tools(mcp, manager)
register_security_tools(mcp, manager)


def _get_homebrew_lldb_paths() -> list[str]:
    """Get LLDB Python paths from Homebrew LLVM installation."""
    paths = []
    # Intel Mac
    intel_base = "/usr/local/opt/llvm/lib"
    # Apple Silicon Mac
    arm_base = "/opt/homebrew/opt/llvm/lib"

    for base in [intel_base, arm_base]:
        if Path(base).exists():
            # Try common Python versions
            for pyver in ["3.13", "3.12", "3.11", "3.10"]:
                lldb_path = f"{base}/python{pyver}/site-packages"
                if Path(lldb_path).exists():
                    paths.append(lldb_path)
    return paths


def _get_homebrew_framework_paths() -> list[str]:
    """Get LLDB framework paths from Homebrew LLVM installation."""
    paths = []
    for base in ["/usr/local/opt/llvm/lib", "/opt/homebrew/opt/llvm/lib"]:
        if Path(base).exists():
            paths.append(base)
    return paths


def _print_lldb_install_help() -> None:
    """Print helpful instructions for installing LLDB."""
    msg = """
LLDB Python module not found. To fix this:

1. Install Homebrew LLVM:
   brew install llvm

2. Add LLVM to your PATH (add to ~/.zshrc):
   export PATH="$(brew --prefix llvm)/bin:$PATH"

3. Alternatively, set LLDB_PYTHON_PATH environment variable:
   export LLDB_PYTHON_PATH="/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
   (Adjust the Python version as needed)

For more details, see: https://github.com/FYTJ/lldb-mcp-server#prerequisites
"""
    # Use stderr to avoid interfering with MCP stdio communication
    print(msg, file=sys.stderr)


def ensure_lldb_env(reexec: bool = False) -> bool:
    """Ensure the LLDB Python module can be imported.

    This function attempts to configure the environment for LLDB Python bindings.
    It supports multiple LLDB sources:
    - LLDB_PYTHON_PATH environment variable (highest priority)
    - Homebrew LLVM on Intel Mac (/usr/local/opt/llvm)
    - Homebrew LLVM on Apple Silicon Mac (/opt/homebrew/opt/llvm)
    - Xcode Command Line Tools
    - config.json configuration

    Args:
        reexec: If True and LLDB import fails, attempt to re-execute the process
                with the correct environment variables.

    Returns:
        True if LLDB was successfully imported, False otherwise.
    """
    try:
        importlib.import_module("lldb")
        logger.info("lldb import ok")
        return True
    except Exception as exc:
        logger.warning("lldb import failed: %s", str(exc))
        if reexec and os.environ.get("LLDB_MCP_REEXECED") != "1":
            env = os.environ.copy()
            project_src = str(Path(__file__).resolve().parents[2])
            existing = env.get("PYTHONPATH", "")
            if project_src not in existing.split(os.pathsep):
                env["PYTHONPATH"] = project_src + (os.pathsep + existing if existing else "")
            candidates = []
            if config.preferred_python_executable:
                candidates.append(config.preferred_python_executable)
            if sys.executable not in candidates:
                candidates.append(sys.executable)

            # Priority 1: LLDB_PYTHON_PATH environment variable
            user_lldb_path = os.environ.get("LLDB_PYTHON_PATH")
            if user_lldb_path and Path(user_lldb_path).exists():
                env["PYTHONPATH"] = user_lldb_path + (os.pathsep + env.get("PYTHONPATH", ""))
                logger.info("Using LLDB_PYTHON_PATH: %s", user_lldb_path)

            # Priority 2: lldb -P command
            try:
                out = subprocess.check_output(["lldb", "-P"], text=True).strip()
                if out:
                    env["PYTHONPATH"] = out + (os.pathsep + env.get("PYTHONPATH", ""))
            except Exception:
                pass

            # Priority 3: Homebrew LLVM paths (Intel and Apple Silicon)
            for p in _get_homebrew_lldb_paths():
                if p not in env.get("PYTHONPATH", ""):
                    env["PYTHONPATH"] = p + (os.pathsep + env.get("PYTHONPATH", ""))

            # Priority 4: config.json paths
            for p in (config.lldb_python_paths or []):
                try:
                    if Path(p).exists():
                        env["PYTHONPATH"] = p + (os.pathsep + env.get("PYTHONPATH", ""))
                except Exception:
                    continue

            # Framework paths
            fwpaths = list(config.lldb_framework_paths or [])
            fwpaths.extend(_get_homebrew_framework_paths())
            try:
                devroot = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
                if devroot:
                    shared = str(Path(devroot) / "../SharedFrameworks")
                    private = str(Path(devroot) / "Library" / "PrivateFrameworks")
                    if Path(shared).exists():
                        fwpaths.append(shared)
                    if Path(private).exists():
                        fwpaths.append(private)
            except Exception:
                pass
            for fp in fwpaths:
                if Path(fp).exists():
                    env["DYLD_FRAMEWORK_PATH"] = fp + (os.pathsep + env.get("DYLD_FRAMEWORK_PATH", ""))
                    env["DYLD_LIBRARY_PATH"] = fp + (os.pathsep + env.get("DYLD_LIBRARY_PATH", ""))
            env["PYTHONUNBUFFERED"] = "1"
            env["LLDB_MCP_REEXECED"] = "1"
            for exe in candidates:
                if Path(exe).exists() or exe == sys.executable:
                    try:
                        os.execvpe(exe, [exe, "-m", "lldb_mcp_server.fastmcp_server", *sys.argv[1:]], env)
                    except Exception:
                        continue

        # Print help message if LLDB is not available
        _print_lldb_install_help()
        return False

    # Build candidate paths for LLDB Python module
    candidates = []

    # Priority 1: LLDB_PYTHON_PATH environment variable
    user_lldb_path = os.environ.get("LLDB_PYTHON_PATH")
    if user_lldb_path:
        candidates.append(user_lldb_path)

    # Priority 2: lldb -P command
    try:
        out = subprocess.check_output(["lldb", "-P"], text=True).strip()
        if out:
            candidates.append(out)
    except Exception:
        pass

    # Priority 3: Homebrew LLVM paths
    candidates.extend(_get_homebrew_lldb_paths())

    # Priority 4: config.json paths
    candidates.extend(list(config.lldb_python_paths or []))

    added = []
    for p in candidates:
        if p and Path(p).exists() and p not in sys.path:
            sys.path.insert(0, p)
            added.append(p)

    # Framework paths
    fw_candidates = list(config.lldb_framework_paths or [])
    fw_candidates.extend(_get_homebrew_framework_paths())
    try:
        devroot = subprocess.check_output(["xcode-select", "-p"], text=True).strip()
        if devroot:
            shared = str(Path(devroot) / "../SharedFrameworks")
            private = str(Path(devroot) / "Library" / "PrivateFrameworks")
            if Path(shared).exists():
                fw_candidates.append(shared)
            if Path(private).exists():
                fw_candidates.append(private)
    except Exception:
        pass

    def _prepend_env(key: str, val: str) -> None:
        cur = os.environ.get(key)
        os.environ[key] = val if not cur else (val + os.pathsep + cur)

    for fp in fw_candidates:
        if Path(fp).exists():
            _prepend_env("DYLD_FRAMEWORK_PATH", fp)
            _prepend_env("DYLD_LIBRARY_PATH", fp)
    try:
        import ctypes

        for fp in fw_candidates:
            lib = Path(fp) / "LLDB.framework" / "LLDB"
            if lib.exists():
                try:
                    ctypes.CDLL(str(lib))
                    logger.info("preloaded LLDB framework from %s", str(lib))
                    break
                except Exception:
                    continue
    except Exception:
        pass
    try:
        importlib.import_module("lldb")
        logger.info(
            "lldb import configured: sys.path added=%s; DYLD_FRAMEWORK_PATH=%s; DYLD_LIBRARY_PATH=%s",
            ",".join(added),
            os.environ.get("DYLD_FRAMEWORK_PATH", ""),
            os.environ.get("DYLD_LIBRARY_PATH", ""),
        )
        return True
    except Exception as exc:
        logger.warning("lldb import still failed: %s", str(exc))
        _print_lldb_install_help()
        return False


def main() -> None:
    """Run the LLDB MCP Server using stdio transport."""
    ensure_lldb_env(reexec=True)
    mcp.run()


if __name__ == "__main__":
    main()
