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
    version="0.3.0",
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


def ensure_lldb_env(reexec: bool = False) -> bool:
    """Ensure the LLDB Python module can be imported using platform providers.

    This function uses platform-specific providers to discover and configure LLDB
    Python bindings. It supports:
    - Platform auto-detection (macOS, Linux, Windows)
    - Distribution-specific paths (Ubuntu, Fedora, Arch, etc.)
    - LLDB_PYTHON_PATH environment variable (highest priority)
    - Platform-specific package managers (Homebrew, apt, dnf, etc.)
    - config.json configuration

    Args:
        reexec: If True and LLDB import fails, attempt to re-execute the process
                with the correct environment variables.

    Returns:
        True if LLDB was successfully imported, False otherwise.
    """
    # Step 1: Try direct import (might already be configured)
    try:
        importlib.import_module("lldb")
        logger.info("lldb import ok")
        return True
    except Exception as exc:
        logger.warning("lldb import failed: %s", str(exc))

    # Step 2: Get platform provider
    from .platform import PlatformDetector, get_provider

    platform_type = PlatformDetector.detect_platform(config.platform_override)
    logger.info("Detected platform: %s", platform_type)

    if platform_type == "unknown":
        logger.error("Unsupported platform detected")
        print("Unsupported platform. LLDB MCP Server requires macOS or Linux.", file=sys.stderr)
        return False

    try:
        provider = get_provider(platform_type, config)
    except ValueError as e:
        logger.error("Platform provider error: %s", str(e))
        print(str(e), file=sys.stderr)
        return False

    # Step 3: Attempt re-execution if requested
    if reexec and os.environ.get("LLDB_MCP_REEXECED") != "1":
        return _attempt_reexec(provider)

    # Step 4: Configure environment in current process
    return _configure_environment(provider)


def _attempt_reexec(provider) -> bool:
    """Attempt to re-execute with corrected environment."""

    env = os.environ.copy()

    # Add project to PYTHONPATH
    project_src = str(Path(__file__).resolve().parents[2])
    existing = env.get("PYTHONPATH", "")
    if project_src not in existing.split(os.pathsep):
        env["PYTHONPATH"] = project_src + (os.pathsep + existing if existing else "")

    # Determine Python executable candidates
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
    for lldb_cmd in provider.get_lldb_command_paths():
        try:
            out = subprocess.check_output([lldb_cmd, "-P"], text=True, stderr=subprocess.DEVNULL).strip()
            if out and Path(out).exists():
                env["PYTHONPATH"] = out + (os.pathsep + env.get("PYTHONPATH", ""))
                logger.info("Using lldb -P path: %s", out)
                break
        except Exception:
            continue

    # Priority 3: Platform-specific paths
    for p in provider.get_lldb_python_paths():
        if p not in env.get("PYTHONPATH", ""):
            env["PYTHONPATH"] = p + (os.pathsep + env.get("PYTHONPATH", ""))

    # Priority 4: Config paths
    for p in (config.lldb_python_paths or []):
        try:
            if Path(p).exists() and p not in env.get("PYTHONPATH", ""):
                env["PYTHONPATH"] = p + (os.pathsep + env.get("PYTHONPATH", ""))
        except Exception:
            continue

    # Framework/library paths
    lib_env_name = provider.get_library_path_env_name()
    fw_env_name = provider.get_framework_path_env_name()

    framework_paths = list(config.lldb_framework_paths or [])
    framework_paths.extend(provider.get_framework_paths())

    for fp in framework_paths:
        if Path(fp).exists():
            # Set library path (LD_LIBRARY_PATH on Linux, DYLD_LIBRARY_PATH on macOS)
            existing_lib = env.get(lib_env_name, "")
            env[lib_env_name] = fp + (os.pathsep + existing_lib if existing_lib else "")

            # Set framework path if applicable (macOS only)
            if fw_env_name:
                existing_fw = env.get(fw_env_name, "")
                env[fw_env_name] = fp + (os.pathsep + existing_fw if existing_fw else "")

    # Platform-specific environment variables
    env.update(provider.get_platform_specific_env())

    # Mark as re-executed
    env["PYTHONUNBUFFERED"] = "1"
    env["LLDB_MCP_REEXECED"] = "1"

    # Attempt re-execution
    for exe in candidates:
        if Path(exe).exists() or exe == sys.executable:
            try:
                logger.info("Re-executing with: %s", exe)
                os.execvpe(exe, [exe, "-m", "lldb_mcp_server.fastmcp_server", *sys.argv[1:]], env)
            except Exception as e:
                logger.debug("Re-exec failed with %s: %s", exe, str(e))
                continue

    # If we get here, re-execution failed
    _print_platform_install_help(provider)
    return False


def _configure_environment(provider) -> bool:
    """Configure environment in current process without re-execution."""
    # Build candidate paths for LLDB Python module
    candidates = []

    # Priority 1: LLDB_PYTHON_PATH environment variable
    user_lldb_path = os.environ.get("LLDB_PYTHON_PATH")
    if user_lldb_path:
        candidates.append(user_lldb_path)

    # Priority 2: lldb -P command
    for lldb_cmd in provider.get_lldb_command_paths():
        try:
            out = subprocess.check_output([lldb_cmd, "-P"], text=True, stderr=subprocess.DEVNULL).strip()
            if out:
                candidates.append(out)
                break
        except Exception:
            continue

    # Priority 3: Platform-specific paths
    candidates.extend(provider.get_lldb_python_paths())

    # Priority 4: Config paths
    candidates.extend(list(config.lldb_python_paths or []))

    # Add valid paths to sys.path
    added = []
    for p in candidates:
        if p and Path(p).exists() and p not in sys.path:
            sys.path.insert(0, p)
            added.append(p)

    # Framework/library paths
    lib_env_name = provider.get_library_path_env_name()
    fw_env_name = provider.get_framework_path_env_name()

    framework_candidates = list(config.lldb_framework_paths or [])
    framework_candidates.extend(provider.get_framework_paths())

    def _prepend_env(key: str, val: str) -> None:
        cur = os.environ.get(key)
        os.environ[key] = val if not cur else (val + os.pathsep + cur)

    for fp in framework_candidates:
        if Path(fp).exists():
            _prepend_env(lib_env_name, fp)
            if fw_env_name:
                _prepend_env(fw_env_name, fp)

    # Preload LLDB library
    provider.preload_lldb_library(framework_candidates)

    # Try to import LLDB
    try:
        importlib.import_module("lldb")
        lib_val = os.environ.get(lib_env_name, "")
        log_msg = f"lldb import configured: sys.path added={','.join(added)}; {lib_env_name}={lib_val}"
        if fw_env_name:
            fw_val = os.environ.get(fw_env_name, "")
            log_msg += f"; {fw_env_name}={fw_val}"
        logger.info(log_msg)
        return True
    except Exception as exc:
        logger.warning("lldb import still failed: %s", str(exc))
        _print_platform_install_help(provider)
        return False


def _print_platform_install_help(provider) -> None:
    """Print platform-specific installation help."""
    if hasattr(provider, "get_install_instructions"):
        print(provider.get_install_instructions(), file=sys.stderr)
    else:
        # Fallback generic message
        print(
            """
LLDB Python module not found. Please install LLDB and set LLDB_PYTHON_PATH.

For more details, see: https://github.com/FYTJ/lldb-mcp-server#prerequisites
""",
            file=sys.stderr,
        )


def main() -> None:
    """Run the LLDB MCP Server using stdio transport."""
    ensure_lldb_env(reexec=True)
    mcp.run()


if __name__ == "__main__":
    main()
