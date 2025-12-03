import os
import re
import shlex
import time
import sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from mcp_client import MCPClient
from config import load_config

def main():
    cfg = load_config()
    target_bin = os.environ.get("TARGET_BIN") or (cfg.get("client") or {}).get("target_bin")
    if not target_bin:
        raise RuntimeError("Set TARGET_BIN or client.target_bin in config.json")
    host = os.environ.get("MCP_HOST") or cfg.get("server_host")
    port = os.environ.get("MCP_PORT") or cfg.get("server_port")
    client = MCPClient(timeout=int(os.environ.get("LLDB_MCP_TIMEOUT", str((cfg.get("client") or {}).get("timeout", 30)))), host=host, port=port)
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
    try:
        tdir = Path(target_bin).resolve().parent
        sdir = tdir / "logs" / "sessions"
        sdir.mkdir(parents=True, exist_ok=True)
        sp = sdir / (time.strftime("%Y%m%d_%H%M%S") + ".log")
        sp.write_text(p.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8", errors="ignore")
        summ = tdir / "logs" / "lldb_summary.log"
        summ.parent.mkdir(parents=True, exist_ok=True)
        with open(summ, "a", encoding="utf-8", errors="ignore") as f:
            f.write("会话结束\n")
    except Exception:
        pass
    client.close()
    print("/compact")

if __name__ == "__main__":
    main()
