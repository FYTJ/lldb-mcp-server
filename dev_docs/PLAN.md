# LLDB MCP Server - Claude Code Integration Plan

## Overview

This plan documents how to integrate LLDB MCP Server into Claude Code using the `/mcp` command and provides both direct Python and optional npm/npx startup configurations.

**Integration Methods:**
1. **Method 1 (Recommended): Direct Python Execution** - 使用 stdio transport 直接启动 Python 模块
2. **Method 2 (Optional): npm/npx Wrapper** - 提供 npm 包装器用于分发和安装
3. **Method 3 (Development): HTTP Server** - HTTP 模式用于开发和测试

---

## Stage 0: Claude Code Integration Setup (COMPLETED ✅)

### Current Status

✅ **All critical integration work is complete:**
- .mcp.json configured with stdio transport
- Python module entry point working (`python3 -m lldb_mcp_server.fastmcp_server`)
- 40 MCP tools ready for use
- Interactive debugging guide created
- Enhanced error messages implemented

### What Conditions Are Already Met

1. ✅ **Python Environment**
   - Python ≥3.10 installed (project uses 3.13)
   - LLDB Python module accessible
   - Virtual environment configured (.venv)

2. ✅ **MCP Configuration**
   - .mcp.json exists in project root
   - stdio transport configured
   - Environment variables defined (LLDB_MCP_ALLOW_LAUNCH, LLDB_MCP_ALLOW_ATTACH)

3. ✅ **Package Structure**
   - pyproject.toml defines package metadata
   - Entry point configured: `lldb-mcp = "lldb_mcp_server.fastmcp_server:main"`
   - Module structure allows `python3 -m` execution

4. ✅ **Tool Implementation**
   - 40 tools implemented across 9 modules
   - FastMCP framework integrated
   - Error handling enhanced
   - Documentation complete

---

## Using `/mcp` Command in Claude Code

### What is `/mcp`?

The `/mcp` command is a built-in Claude Code command for managing MCP server connections:
- **List servers**: View all configured MCP servers
- **Authenticate**: Handle OAuth for remote servers
- **Remove servers**: Disconnect from MCP servers

### Quick Start with Current Configuration

Your `.mcp.json` file is already properly configured! Here's how to verify and use it:

**Step 1: Verify Configuration**
```bash
cd /Users/zhuyanbo/PycharmProjects/lldb-mcp-server
cat .mcp.json
```

Expected output:
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

**Step 2: Start Claude Code in Project Directory**
```bash
cd /Users/zhuyanbo/PycharmProjects/lldb-mcp-server
claude-code
```

**Step 3: Use `/mcp` Command to Verify Connection**

In Claude Code, run:
```
/mcp list
```

Expected output:
```
Connected MCP Servers:
- lldb-debugger (stdio, local)
  Status: Connected
  Tools: 40 available
```

**Step 4: Test LLDB Tools**

Ask Claude:
```
List all LLDB MCP tools available
```

Expected: Should see all 40 tools (lldb_initialize, lldb_createTarget, etc.)

**Step 5: Run Interactive Debugging**

Ask Claude:
```
Debug the binary at examples/client/c_test/null_deref/null_deref

Requirements:
1. Use LLDB MCP tools only
2. Find the crash location
3. Explain the bug
```

---

## Method 1: Direct Python Execution (Recommended) ✅

### Why This is Recommended

Your current setup already uses this method. It's optimal because:

1. **No extra dependencies** - Direct Python execution, no npm/node required
2. **Faster startup** - No wrapper overhead
3. **Virtual environment friendly** - Works seamlessly with .venv
4. **Simpler debugging** - Direct Python execution is easier to trace
5. **Best practice** - Recommended by Claude Code documentation

### Current Configuration Analysis

**File: `.mcp.json`**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "python3",              // ✅ Direct Python execution
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],  // ✅ Module execution
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",   // ✅ Security control
        "LLDB_MCP_ALLOW_ATTACH": "1"    // ✅ Security control
      }
    }
  }
}
```

**What Makes This Configuration Optimal:**

1. **Module Execution (`-m`)**
   - Uses Python's module resolution
   - Works regardless of current directory
   - Automatically finds installed package

2. **Environment Variables**
   - `LLDB_MCP_ALLOW_LAUNCH` - Enables process launching
   - `LLDB_MCP_ALLOW_ATTACH` - Enables process attachment
   - Security-first approach (both disabled by default)

3. **Stdio Transport**
   - Claude Code spawns server as subprocess
   - Direct communication via stdin/stdout
   - Automatic lifecycle management

### Alternative: Using Virtual Environment Python

If you want to explicitly use the virtual environment Python:

**File: `.mcp.json` (alternative)**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/.venv/bin/python",
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**When to use this:**
- Multiple Python versions on system
- Want explicit control over which Python
- Reproducibility across team members

### Alternative: Using Installed Entry Point

If package is installed (via `uv pip install -e .`):

**File: `.mcp.json` (alternative)**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "lldb-mcp",  // Uses entry point from pyproject.toml
      "args": [],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**Requirements:**
- Package must be installed: `uv pip install -e .`
- Entry point defined in pyproject.toml (✅ already done)

---

## Method 2: npm/npx Wrapper (Optional)

### When to Use npm/npx Wrapper

Consider using npm/npx wrapper if:
- Distributing to users who prefer npm ecosystem
- Want single-command installation: `npx lldb-mcp-server`
- Publishing to npm registry alongside Smithery
- Users unfamiliar with Python package management

**Important:** This is NOT recommended over direct Python execution for this project because:
- Adds extra dependency (Node.js/npm)
- Slower startup (npm resolution overhead)
- More complex troubleshooting
- Python users typically prefer pip/uv

### Implementation Plan for npm Wrapper

If you want to add npm/npx support as an additional installation method:

#### Step 1: Create package.json

**File: `package.json`** (to create)
```json
{
  "name": "lldb-mcp-server",
  "version": "0.2.0",
  "description": "LLDB debugging MCP server for Claude Code",
  "type": "module",
  "bin": {
    "lldb-mcp-server": "./bin/lldb-mcp-server.js"
  },
  "scripts": {
    "postinstall": "node bin/install-deps.js",
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [
    "lldb",
    "debugging",
    "mcp",
    "claude",
    "anthropic"
  ],
  "author": "FYTJ <simonzhuyb@163.com>",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/FYTJ/lldb-mcp-server.git"
  },
  "engines": {
    "node": ">=16"
  },
  "files": [
    "bin/",
    "src/",
    "pyproject.toml",
    "README.md"
  ]
}
```

#### Step 2: Create npm Wrapper Script

**File: `bin/lldb-mcp-server.js`** (to create)
```javascript
#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkgRoot = join(__dirname, '..');

const python = 'python3';
const args = ['-m', 'lldb_mcp_server.fastmcp_server'];

const env = {
  ...process.env,
  PYTHONPATH: join(pkgRoot, 'src'),
  LLDB_MCP_ALLOW_LAUNCH: process.env.LLDB_MCP_ALLOW_LAUNCH || '1',
  LLDB_MCP_ALLOW_ATTACH: process.env.LLDB_MCP_ALLOW_ATTACH || '1'
};

const child = spawn(python, args, {
  stdio: 'inherit',
  env: env,
  cwd: pkgRoot
});

child.on('exit', (code) => process.exit(code || 0));
child.on('error', (err) => {
  console.error('Failed to start LLDB MCP server:', err.message);
  process.exit(1);
});
```

**Make it executable:**
```bash
chmod +x bin/lldb-mcp-server.js
```

#### Step 3: Create Install Dependencies Script

**File: `bin/install-deps.js`** (to create)
```javascript
#!/usr/bin/env node

import { execSync } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const pkgRoot = join(__dirname, '..');

console.log('Installing LLDB MCP Server Python dependencies...');

try {
  try {
    execSync('uv --version', { stdio: 'ignore' });
    console.log('Using uv for installation');
    execSync('uv pip install -e .', { cwd: pkgRoot, stdio: 'inherit' });
  } catch {
    console.log('Using pip for installation');
    execSync('pip3 install -e .', { cwd: pkgRoot, stdio: 'inherit' });
  }
  console.log('✅ Python dependencies installed successfully');
} catch (error) {
  console.error('❌ Failed to install Python dependencies:');
  console.error(error.message);
  console.error('\nPlease ensure Python ≥3.10 and pip are installed');
  process.exit(1);
}
```

**Make it executable:**
```bash
chmod +x bin/install-deps.js
```

#### Step 4: Configure Claude Code for npx

**File: `.mcp.json.npx`** (create as example)
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "npx",
      "args": ["-y", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**Windows configuration:**
```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

#### Step 5: Test Locally

```bash
# Link package locally
npm link

# Test npx execution
npx lldb-mcp-server

# Test with Claude Code
cp .mcp.json.npx .mcp.json
claude-code
# In Claude: /mcp list
```

---

## Method 3: HTTP Server Mode (Development)

### When to Use HTTP Mode

Use HTTP mode for:
- Manual testing with curl/Postman
- Debugging server issues
- Running standalone Python scripts
- Multiple concurrent clients

**Do NOT use HTTP mode for:**
- Normal Claude Code debugging (use stdio instead)
- Production usage (stdio is more secure)

### Configuration

**File: `.mcp.json.http`** (example already exists)
```json
{
  "mcpServers": {
    "lldb-debugger-http": {
      "transport": {
        "type": "http",
        "url": "http://127.0.0.1:8765"
      }
    }
  }
}
```

### Usage

**Start HTTP server:**
```bash
cd /Users/zhuyanbo/PycharmProjects/lldb-mcp-server
source .venv/bin/activate

LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  python -m lldb_mcp_server.fastmcp_server \
  --transport http \
  --port 8765
```

---

## Verification Steps

### Verify Method 1 (Direct Python - Current Setup)

```bash
# 1. Start Claude Code in project directory
cd /Users/zhuyanbo/PycharmProjects/lldb-mcp-server
claude-code

# 2. Verify MCP server connection
# In Claude Code:
/mcp list

# Expected: lldb-debugger shown as connected with 40 tools

# 3. Test tool availability
# In Claude Code, ask:
"List all LLDB MCP tools"

# Expected: See all 40 tools

# 4. Test interactive debugging
# In Claude Code, ask:
"Debug examples/client/c_test/null_deref/null_deref and find the bug"

# Expected: Claude uses lldb_initialize, lldb_createTarget, etc.
```

### Verify Method 2 (npm/npx - If Implemented)

```bash
# 1. Test local npm package
npm link
npx lldb-mcp-server

# Expected: Server starts successfully

# 2. Configure Claude Code
cp .mcp.json.npx .mcp.json

# 3. Test with Claude Code
claude-code
# In Claude: /mcp list

# Expected: lldb-debugger connected via npx

# 4. Test publishing
npm publish --dry-run

# Expected: No errors, shows what would be published
```

### Verify Method 3 (HTTP - Development Only)

```bash
# 1. Start HTTP server
LLDB_MCP_ALLOW_LAUNCH=1 python -m lldb_mcp_server.fastmcp_server --transport http --port 8765

# 2. Test health endpoint
curl http://127.0.0.1:8765/health

# Expected: {"status": "healthy"}

# 3. Configure Claude Code
cp .mcp.json.http .mcp.json
claude-code

# 4. Verify connection
# In Claude: /mcp list

# Expected: lldb-debugger-http connected
```

---

## Summary

### Current Status (Method 1 - Recommended) ✅

Your system is READY to use:
- ✅ .mcp.json configured with stdio transport
- ✅ Python module execution working
- ✅ All 40 tools available
- ✅ Security controls in place

**To use with Claude Code:**
1. Navigate to project directory
2. Run `claude-code`
3. Use `/mcp list` to verify connection
4. Start debugging with LLDB tools

### Optional Enhancements

If you want npm/npx support (Method 2):
- [ ] Create package.json
- [ ] Create wrapper scripts (bin/lldb-mcp-server.js, bin/install-deps.js)
- [ ] Make scripts executable
- [ ] Test with npm link
- [ ] Optional: Publish to npm registry

### Files to Create for npm/npx Support

| File | Purpose |
|------|---------|
| `package.json` | npm package metadata |
| `bin/lldb-mcp-server.js` | npm executable wrapper |
| `bin/install-deps.js` | Python dependency installer |
| `.mcp.json.npx` | Example npx configuration |

### Files Already Exist

| File | Status |
|------|--------|
| `.mcp.json` | ✅ Configured for stdio |
| `.mcp.json.http` | ✅ Example HTTP config |
| `pyproject.toml` | ✅ Python package metadata |
| `smithery.yaml` | ✅ Smithery marketplace config |

---

## Next Steps

### Immediate (Use Current Setup)

1. ✅ Configuration complete - no changes needed
2. Test with Claude Code: `claude-code` in project directory
3. Use `/mcp list` to verify connection
4. Start debugging with interactive tools

### Optional (Add npm/npx Support)

1. Create package.json and wrapper scripts
2. Test locally with npm link
3. Publish to npm registry (optional)
4. Document npm installation method in README

### Future (After Testing)

1. Publish to Smithery marketplace
2. Document real-world debugging examples
3. Gather user feedback
4. Enhance skill documentation

---

## Common MCP Commands Reference

```bash
# List all MCP servers
claude mcp list

# Get details for specific server
claude mcp get lldb-debugger

# Remove MCP server
claude mcp remove lldb-debugger

# Add MCP server (stdio)
claude mcp add --transport stdio lldb-debugger -- python3 -m lldb_mcp_server.fastmcp_server

# Add MCP server with environment variables
claude mcp add --transport stdio lldb-debugger --env LLDB_MCP_ALLOW_LAUNCH=1 -- python3 -m lldb_mcp_server.fastmcp_server

# Reset project-scoped server approvals
claude mcp reset-project-choices
```

---

## Troubleshooting

### Issue: `/mcp list` shows no servers

**Solution:**
1. Verify .mcp.json exists in project root
2. Verify you started Claude Code in project directory
3. Check .mcp.json syntax (valid JSON)

### Issue: Server shows "Connection failed"

**Solution:**
1. Test Python module directly: `python3 -m lldb_mcp_server.fastmcp_server --help`
2. Verify virtual environment active
3. Check LLDB Python module: `python -c "import lldb; print('OK')"`
4. Verify package installed: `uv pip list | grep lldb-mcp-server`

### Issue: Tools not visible in Claude

**Solution:**
1. Run `/mcp list` to verify server connected
2. Ask Claude: "List all LLDB MCP tools"
3. Check server logs for errors
4. Restart Claude Code

### Issue: Permission denied errors

**Solution:**
1. Verify environment variables set in .mcp.json
2. Check LLDB_MCP_ALLOW_LAUNCH and LLDB_MCP_ALLOW_ATTACH are "1"
3. Restart Claude Code after config changes

---

## Documentation Updates Needed

After implementing npm/npx support (if desired), update:

**File: `README.md`**
- Add npm installation method
- Add npx usage example
- Document both Python and npm workflows

**File: `dev_docs/PLAN.md`**
- Mark Stage 0 as complete
- Update with npm/npx implementation status
- Document verification results

---

## Absolute File Paths Reference

**Configuration:**
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/.mcp.json` (stdio config)
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/.mcp.json.http` (HTTP config)
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/.mcp.json.npx` (to create)

**Package:**
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/pyproject.toml` (Python metadata)
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/package.json` (to create)

**Scripts:**
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/bin/lldb-mcp-server.js` (to create)
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/bin/install-deps.js` (to create)

**Server Entry Point:**
- `/Users/zhuyanbo/PycharmProjects/lldb-mcp-server/src/lldb_mcp_server/fastmcp_server.py`
