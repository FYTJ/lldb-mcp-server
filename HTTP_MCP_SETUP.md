# HTTP MCP Server Setup Guide

This guide explains how to run LLDB MCP Server in HTTP mode for development and testing.

## Important: When to Use HTTP vs Stdio

### Stdio Mode (Recommended for Claude Code/Desktop)
**Use when:** Running Claude Code or Claude Desktop for debugging

**Configuration:** See `.mcp.json` in the project root

**Pros:**
- Tools automatically available in Claude
- No separate server process needed
- Simple configuration
- Automatically starts/stops with Claude

**Cons:**
- Cannot inspect server manually
- One instance per Claude session

### HTTP Mode (For Development/Testing)
**Use when:**
- Testing MCP server manually with curl
- Debugging server issues
- Running standalone Python scripts
- Developing MCP server features

**Configuration:** See `.mcp.json.http` in the project root

**Pros:**
- Server runs independently
- Can inspect with browser/curl
- Multiple clients can connect
- Easier to debug server issues

**Cons:**
- Requires separate terminal for server
- Must manually start/stop server
- **Does NOT work with Claude Code for interactive debugging**

**IMPORTANT:** HTTP mode does NOT allow Claude Code to use MCP tools directly for debugging. Use stdio mode (`.mcp.json`) for that.

---

This guide covers HTTP mode setup for development/testing purposes only.

## Step 1: Start MCP Server in HTTP Mode

Open a terminal and run:

```bash
cd /Users/zhuyanbo/PycharmProjects/lldb-mcp-server
source .venv/bin/activate

# Start HTTP server on port 8765
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  python -m lldb_mcp_server.fastmcp_server \
  --transport http \
  --host 127.0.0.1 \
  --port 8765
```

You should see output like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765
```

**Keep this terminal running** - the server needs to stay active.

## Step 2: Configure Claude Code

### Option A: Project-Level Configuration (Recommended)

Use the example HTTP configuration file:

**File:** `.mcp.json.http` (example provided in project root)

To use it, copy it to `.mcp.json`:

```bash
cp .mcp.json.http .mcp.json
```

**Note:** The default `.mcp.json` uses stdio mode. Only use HTTP configuration for development/testing.

This configuration is automatically detected when you run Claude Code in this directory.

### Option B: Global Configuration

For access from any directory, add to `~/.config/claude/mcp.json`:

```bash
# Create config directory if it doesn't exist
mkdir -p ~/.config/claude

# Create or edit mcp.json
cat > ~/.config/claude/mcp.json << 'EOF'
{
  "mcpServers": {
    "lldb-debugger": {
      "transport": {
        "type": "http",
        "url": "http://127.0.0.1:8765"
      }
    }
  }
}
EOF
```

## Step 3: Start a New Claude Code Session

In a **new terminal** (keep the MCP server running in the first one):

```bash
cd /Users/zhuyanbo/PycharmProjects/lldb-mcp-server

# Start Claude Code
claude-code
```

Or if you want to start with a specific prompt:

```bash
claude-code "List available MCP tools"
```

## Step 4: Verify MCP Connection

In the Claude Code session, ask:

```
What MCP tools are available?
```

You should see the 40 LLDB tools listed:
- lldb_initialize
- lldb_createTarget
- lldb_launch
- ... (37 more tools)

## Step 5: Test Debugging

Try a simple debugging session:

```
Debug the binary at /Users/zhuyanbo/PycharmProjects/lldb-mcp-server/examples/client/c_test/null_deref/null_deref

REQUIREMENTS:
1. Use LLDB MCP tools only (no source code)
2. After debugging, use lldb_getTranscript
```

## Troubleshooting

### MCP Server Not Responding

**Check server is running:**
```bash
# In another terminal
curl http://127.0.0.1:8765/health
```

Should return:
```json
{"status": "healthy"}
```

**Check server logs** in the terminal where you started the server.

### Claude Code Can't Find MCP Server

**Verify configuration file:**
```bash
# Check project config
cat .mcp.json

# Or check global config
cat ~/.config/claude/mcp.json
```

**Restart Claude Code** after changing configuration.

### Port Already in Use

If port 8765 is occupied, use a different port:

```bash
# Start server on different port
LLDB_MCP_ALLOW_LAUNCH=1 python -m lldb_mcp_server.fastmcp_server \
  --transport http --port 8766
```

Then update `.mcp.json`:
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "transport": {
        "type": "http",
        "url": "http://127.0.0.1:8766"
      }
    }
  }
}
```

### Firewall Issues

Ensure localhost connections are allowed:
```bash
# macOS - check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

## Configuration Options

### Different Host/Port

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "transport": {
        "type": "http",
        "url": "http://localhost:9000"
      }
    }
  }
}
```

Server command:
```bash
python -m lldb_mcp_server.fastmcp_server --transport http --port 9000
```

### Multiple MCP Servers

You can run multiple MCP servers on different ports:

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "transport": {
        "type": "http",
        "url": "http://127.0.0.1:8765"
      }
    },
    "other-tool": {
      "transport": {
        "type": "http",
        "url": "http://127.0.0.1:8766"
      }
    }
  }
}
```

## Comparison: HTTP vs Stdio

### HTTP Mode (Current Setup)

**Pros:**
- Server runs independently
- Can be accessed from multiple clients
- Easy to debug with curl/browser
- Can run on remote machine

**Cons:**
- Requires keeping terminal open
- Extra step to start server

**Use cases:**
- Testing and development
- Remote debugging
- Multiple concurrent sessions

### Stdio Mode

**Pros:**
- Auto-starts with Claude
- No separate server process
- Simpler configuration

**Cons:**
- One instance per Claude session
- Harder to debug
- Can't share across sessions

**Configuration for stdio:**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "python3",
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

## Testing the Setup

### 1. Quick Health Check

```bash
# Test HTTP endpoint
curl http://127.0.0.1:8765/health
```

### 2. List Tools

In Claude Code:
```
List all available lldb_ tools
```

### 3. Run Simple Test

```
Initialize an LLDB session and list all sessions
```

Expected behavior:
- Claude calls lldb_initialize
- Claude calls lldb_listSessions
- Shows session ID

## Next Steps

After successful connection, proceed with testing:

1. **Run verification tests** - See `examples/client/c_test/TESTING_GUIDE.md`
2. **Test with sample programs** - 8 test programs available
3. **Verify MCP usage** - Use `scripts/verify_mcp_usage.py`

## Quick Reference

**Start server:**
```bash
LLDB_MCP_ALLOW_LAUNCH=1 python -m lldb_mcp_server.fastmcp_server --transport http --port 8765
```

**Config file location:**
- Project: `.mcp.json` (current directory)
- Global: `~/.config/claude/mcp.json`

**Health check:**
```bash
curl http://127.0.0.1:8765/health
```

**Test prompt:**
```
List available LLDB MCP tools
```
