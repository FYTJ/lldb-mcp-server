import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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


@mcp.custom_route("/tools/list", methods=["POST"], include_in_schema=False)
async def tools_list_route(request: Request) -> JSONResponse:
    """Compatibility endpoint for simple HTTP tool listing."""
    tools = await mcp._list_tools_mcp()
    return JSONResponse({"tools": [tool.model_dump(by_alias=True) for tool in tools]})


@mcp.custom_route("/tools/call", methods=["POST"], include_in_schema=False)
async def tools_call_route(request: Request) -> JSONResponse:
    """Compatibility endpoint for simple HTTP tool calls."""
    payload = await request.json()
    name = payload.get("name")
    if not name:
        return JSONResponse({"error": {"message": "Missing tool name"}}, status_code=400)
    arguments = payload.get("arguments") or {}
    try:
        result = await mcp._tool_manager.call_tool(key=name, arguments=arguments)
    except Exception as exc:
        return JSONResponse({"error": {"message": str(exc)}}, status_code=500)
    if result.structured_content is not None:
        return JSONResponse({"result": result.structured_content})
    return JSONResponse({"result": result.content})


def ensure_lldb_env(reexec: bool = False) -> bool:
    """Ensure the LLDB Python module can be imported."""
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
            try:
                out = subprocess.check_output(["lldb", "-P"], text=True).strip()
                if out:
                    env["PYTHONPATH"] = out + (os.pathsep + env.get("PYTHONPATH", ""))
            except Exception:
                pass
            for p in (config.lldb_python_paths or []):
                try:
                    if Path(p).exists():
                        env["PYTHONPATH"] = p + (os.pathsep + env.get("PYTHONPATH", ""))
                except Exception:
                    continue
            fwpaths = list(config.lldb_framework_paths or [])
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
        return False
    candidates = []
    try:
        out = subprocess.check_output(["lldb", "-P"], text=True).strip()
        if out:
            candidates.append(out)
    except Exception:
        pass
    candidates.extend(list(config.lldb_python_paths or []))
    added = []
    for p in candidates:
        if p and Path(p).exists() and p not in sys.path:
            sys.path.insert(0, p)
            added.append(p)
    fw_candidates = list(config.lldb_framework_paths or [])
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
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="LLDB MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP/SSE host address")
    parser.add_argument("--port", type=int, default=8765, help="HTTP/SSE port")
    args = parser.parse_args()

    ensure_lldb_env(reexec=True)

    if args.transport == "stdio":
        mcp.run()
    elif args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
