#!/usr/bin/env python3
"""
Debug null_deref binary using LLDB MCP Server
"""
import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client import MCPClient

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(result):
    """Pretty print MCP tool result"""
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
    else:
        print(result)

def main():
    # Initialize MCP client
    print_section("Connecting to LLDB MCP Server")
    client = MCPClient()
    print("✓ Connected to MCP server")

    # Get absolute path to binary
    binary_path = os.path.abspath("null_deref/null_deref")
    print(f"✓ Binary: {binary_path}")

    # Step 1: Initialize session
    print_section("Step 1: Initialize LLDB Session")
    session_id = client.init_session()
    print(f"✓ Session initialized: {session_id}")

    # Step 2: Create target
    print_section("Step 2: Create Target")
    result = client.create_target(session_id, binary_path)
    print_result(result)

    # Step 3: Launch program
    print_section("Step 3: Launch Program")
    result = client.launch(session_id)
    print_result(result)

    # Step 4: Poll for events
    print_section("Step 4: Poll Events")
    result = client.tools_call("lldb_pollEvents", {"sessionId": session_id})
    print_result(result)

    # Step 5: Get threads
    print_section("Step 5: Get Thread Information")
    result = client.tools_call("lldb_threads", {"sessionId": session_id})
    print_result(result)

    # Step 6: Get stack trace
    print_section("Step 6: Get Stack Trace")
    result = client.tools_call("lldb_stackTrace", {"sessionId": session_id})
    print_result(result)

    # Step 7: Get frames
    print_section("Step 7: Get Frame Details")
    try:
        result = client.tools_call("lldb_frames", {"sessionId": session_id})
        print_result(result)
    except Exception as e:
        print(f"⚠ Error getting frames: {e}")

    # Step 8: Read registers
    print_section("Step 8: Read Registers")
    try:
        result = client.tools_call("lldb_readRegisters", {"sessionId": session_id})
        print_result(result)
    except Exception as e:
        print(f"⚠ Error reading registers: {e}")

    # Step 9: Disassemble crash location
    print_section("Step 9: Disassemble Crash Location")
    try:
        result = client.tools_call("lldb_disassemble", {
            "sessionId": session_id,
            "count": 20
        })
        print_result(result)
    except Exception as e:
        print(f"⚠ Error disassembling: {e}")

    # Step 10: Analyze crash
    print_section("Step 10: Analyze Crash")
    try:
        result = client.tools_call("lldb_analyzeCrash", {"sessionId": session_id})
        print_result(result)
    except Exception as e:
        print(f"⚠ Error analyzing crash: {e}")

    # Step 11: Evaluate expressions to find null pointer
    print_section("Step 11: Evaluate Expressions")
    try:
        # Try to evaluate some common variables
        result = client.tools_call("lldb_evaluate", {
            "sessionId": session_id,
            "expression": "ptr"
        })
        print("ptr =", result)
    except Exception as e:
        print(f"⚠ Error evaluating: {e}")

    # Step 12: Get debugging transcript
    print_section("Step 12: Get Debugging Transcript")
    try:
        result = client.tools_call("lldb_getTranscript", {"sessionId": session_id})
        print_result(result)
    except Exception as e:
        print(f"⚠ Error getting transcript: {e}")

    print_section("Debugging Complete")
    return session_id

if __name__ == "__main__":
    session_id = main()
