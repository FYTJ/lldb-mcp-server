import os
import re
import shlex
import time
from pathlib import Path
from mcp_client import MCPClient
from config import load_config

def main():
    cfg = load_config()
    target_bin = os.environ.get("TARGET_BIN") or (cfg.get("client") or {}).get("target_bin")
    if not target_bin:
        raise RuntimeError("Set TARGET_BIN or client.target_bin in config.json")
    host = os.environ.get("MCP_HOST") or cfg.get("server_host")
    port = os.environ.get("MCP_PORT") or cfg.get("server_port")
    unix_socket = os.environ.get("MCP_UNIX_SOCKET") or (cfg.get("client") or {}).get("unix_socket")
    server_cmd_env = os.environ.get("LLDB_MCP_SERVER_CMD")
    project_root = os.environ.get("LLDB_MCP_PROJECT_ROOT") or cfg.get("project_root")
    src_path = os.environ.get("LLDB_MCP_SRC") or cfg.get("src_path")
    server_cmd = shlex.split(server_cmd_env) if server_cmd_env else None
    extra_env = {}
    if src_path:
        extra_env["PYTHONPATH"] = src_path
    client = MCPClient(server_cmd=server_cmd, cwd=project_root or None, extra_env=extra_env, timeout=int(os.environ.get("LLDB_MCP_TIMEOUT", str((cfg.get("client") or {}).get("timeout", 30)))), project_root=project_root, src_path=src_path, host=host, port=port, unix_socket=unix_socket)
    sid = client.init_session()
    client.create_target(sid, target_bin)
    client.command(sid, "breakpoint set --name main")
    lr = client.launch(sid, [])
    launched = isinstance(lr, dict) and (lr.get("pid") is not None)
    ok = False
    if launched:
        for _ in range(10):
            r = client.tools_call("lldb.threads", {"sessionId": sid})
            if r and r.get("threads"):
                ok = True
                break
            time.sleep(0.2)
    print(client.command(sid, "expr 1+1").get("transcript", ""))
    t2 = client.command(sid, "expr &x").get("transcript", "")
    print(t2)
    m = re.search(r"0x[0-9a-fA-F]+", t2)
    if m and ok:
        addr = int(m.group(0), 16)
        print(client.set_watchpoint(sid, addr, 4, True, True).get("watchpointId", 0))
        print(client.read_memory(sid, addr, 32).get("bytes", ""))
    if launched and ok:
        rr = client.command(sid, "register read").get("transcript", "")
        print(rr)
        pc = client.command(sid, "process continue").get("transcript", "")
        print(pc)
    tp = client.transcript_path(sid)
    print("Transcript:", tp)
    p = Path(tp)
    if p.exists():
        print(p.read_text(encoding="utf-8", errors="ignore"))
    client.close()

if __name__ == "__main__":
    main()

