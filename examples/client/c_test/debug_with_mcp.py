#!/usr/bin/env python3
"""
Debug script that uses LLDB MCP Server HTTP API
"""
import requests
import json
import time

MCP_URL = "http://127.0.0.1:8765"

def call_mcp_tool(tool_name, arguments=None):
    """Call an MCP tool via HTTP"""
    if arguments is None:
        arguments = {}

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    response = requests.post(f"{MCP_URL}/mcp/v1", json=payload)
    result = response.json()
    return result

def main():
    # Get absolute path to binary
    import os
    binary_path = os.path.abspath("null_deref/null_deref")
    print(f"Debugging binary: {binary_path}\n")

    # Step 1: Initialize session
    print("=" * 60)
    print("Step 1: Initialize LLDB session")
    print("=" * 60)
    result = call_mcp_tool("lldb_initialize")
    print(json.dumps(result, indent=2))

    if "result" in result and "content" in result["result"]:
        for content in result["result"]["content"]:
            if "text" in content:
                data = json.loads(content["text"])
                session_id = data.get("session_id")
                print(f"\nSession ID: {session_id}\n")

    # Step 2: Create target
    print("=" * 60)
    print("Step 2: Create target with binary")
    print("=" * 60)
    result = call_mcp_tool("lldb_createTarget", {
        "session_id": session_id,
        "executable": binary_path
    })
    print(json.dumps(result, indent=2))

    # Step 3: Launch program
    print("\n" + "=" * 60)
    print("Step 3: Launch program")
    print("=" * 60)
    result = call_mcp_tool("lldb_launch", {
        "session_id": session_id
    })
    print(json.dumps(result, indent=2))

    # Step 4: Poll for events
    print("\n" + "=" * 60)
    print("Step 4: Poll for events")
    print("=" * 60)
    time.sleep(0.5)  # Give it time to crash
    result = call_mcp_tool("lldb_pollEvents", {
        "session_id": session_id
    })
    print(json.dumps(result, indent=2))

    # Step 5: Get stack trace
    print("\n" + "=" * 60)
    print("Step 5: Get stack trace")
    print("=" * 60)
    result = call_mcp_tool("lldb_stackTrace", {
        "session_id": session_id
    })
    print(json.dumps(result, indent=2))

    # Step 6: Get thread info
    print("\n" + "=" * 60)
    print("Step 6: Get thread info")
    print("=" * 60)
    result = call_mcp_tool("lldb_threads", {
        "session_id": session_id
    })
    print(json.dumps(result, indent=2))

    # Step 7: Analyze crash
    print("\n" + "=" * 60)
    print("Step 7: Analyze crash")
    print("=" * 60)
    result = call_mcp_tool("lldb_analyzeCrash", {
        "session_id": session_id
    })
    print(json.dumps(result, indent=2))

    # Step 8: Disassemble crash location
    print("\n" + "=" * 60)
    print("Step 8: Disassemble crash location")
    print("=" * 60)
    result = call_mcp_tool("lldb_disassemble", {
        "session_id": session_id,
        "count": 20
    })
    print(json.dumps(result, indent=2))

    # Step 9: Read registers
    print("\n" + "=" * 60)
    print("Step 9: Read registers")
    print("=" * 60)
    result = call_mcp_tool("lldb_readRegisters", {
        "session_id": session_id
    })
    print(json.dumps(result, indent=2))

    # Step 10: Get transcript
    print("\n" + "=" * 60)
    print("Step 10: Get debugging transcript")
    print("=" * 60)
    result = call_mcp_tool("lldb_getTranscript", {
        "session_id": session_id
    })
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("Debugging session complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
