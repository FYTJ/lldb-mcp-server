#!/usr/bin/env python3
"""Verify AI used MCP tools instead of source code analysis."""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List


def verify_transcript(transcript_text: str, scenario: str) -> Dict:
    """Verify transcript contains required MCP tool calls.

    Args:
        transcript_text: The debugging transcript text
        scenario: The test scenario type (crash, breakpoint, memory)

    Returns:
        Dictionary with verification results
    """

    # Parse transcript for tool calls
    required_base = [
        "lldb_initialize",
        "lldb_createTarget",
        "lldb_launch",
        "lldb_pollEvents",
    ]

    scenario_tools = {
        "crash": ["lldb_stackTrace", "lldb_analyzeCrash"],
        "breakpoint": ["lldb_setBreakpoint", "lldb_evaluate"],
        "memory": ["lldb_readMemory", "lldb_setWatchpoint"],
    }

    required = required_base + scenario_tools.get(scenario, [])

    # Find which tools were actually called
    found_tools = []
    for tool in required:
        if tool in transcript_text:
            found_tools.append(tool)

    # Check for source code file reads (should NOT happen)
    source_read_patterns = [
        r'Read.*\.c\b',           # Read tool on .c files
        r'cat\s+.*\.c\b',         # cat command on .c files
        r'open.*\.c\b',           # open function on .c files
        r'Glob.*\.c\b',           # Glob tool for .c files
    ]

    source_reads = []
    for pattern in source_read_patterns:
        matches = re.findall(pattern, transcript_text, re.IGNORECASE)
        source_reads.extend(matches)

    # Calculate missing tools
    missing_tools = list(set(required) - set(found_tools))

    # Determine if test is valid
    # Valid if: found at least 70% of required tools AND no source reads
    min_required_tools = int(len(required) * 0.7)
    has_enough_tools = len(found_tools) >= min_required_tools
    no_source_reads = len(source_reads) == 0

    valid = has_enough_tools and no_source_reads

    return {
        "scenario": scenario,
        "required_tools": required,
        "found_tools": found_tools,
        "missing_tools": missing_tools,
        "source_reads": source_reads,
        "tools_found_count": len(found_tools),
        "tools_required_count": len(required),
        "tools_coverage": f"{len(found_tools)}/{len(required)} ({int(len(found_tools)/len(required)*100)}%)",
        "valid": valid,
        "has_enough_tools": has_enough_tools,
        "no_source_reads": no_source_reads,
    }


def print_results(result: Dict):
    """Print verification results in a human-readable format."""

    print("\n" + "="*60)
    print(f"MCP Usage Verification Results - Scenario: {result['scenario']}")
    print("="*60)

    print(f"\nTool Coverage: {result['tools_coverage']}")
    print(f"  Required tools: {result['tools_required_count']}")
    print(f"  Found tools: {result['tools_found_count']}")

    if result['found_tools']:
        print(f"\n✅ Found MCP Tool Calls:")
        for tool in result['found_tools']:
            print(f"  - {tool}")

    if result['missing_tools']:
        print(f"\n⚠️  Missing MCP Tool Calls:")
        for tool in result['missing_tools']:
            print(f"  - {tool}")

    if result['source_reads']:
        print(f"\n❌ Source Code Reads Detected (INVALID):")
        for read in result['source_reads']:
            print(f"  - {read}")
    else:
        print(f"\n✅ No source code reads detected")

    print("\n" + "="*60)
    if result['valid']:
        print("✅ PASS: AI used MCP tools correctly")
        print("="*60)
    else:
        print("❌ FAIL: AI did not use MCP tools correctly")
        print("="*60)

        if not result['has_enough_tools']:
            print(f"  Reason: Insufficient tool usage ({result['tools_found_count']}/{result['tools_required_count']} tools)")
        if not result['no_source_reads']:
            print(f"  Reason: Source code was accessed ({len(result['source_reads'])} reads)")


def main():
    """Main entry point."""

    if len(sys.argv) != 3:
        print("Usage: verify_mcp_usage.py <transcript_file> <scenario>")
        print("\nScenarios:")
        print("  crash      - Crash detection and analysis")
        print("  breakpoint - Breakpoint-based debugging")
        print("  memory     - Memory inspection and watchpoints")
        print("\nExample:")
        print("  python scripts/verify_mcp_usage.py logs/session_123.txt crash")
        sys.exit(1)

    transcript_file = Path(sys.argv[1])
    scenario = sys.argv[2]

    # Validate inputs
    if not transcript_file.exists():
        print(f"Error: Transcript file not found: {transcript_file}")
        sys.exit(1)

    if scenario not in ["crash", "breakpoint", "memory"]:
        print(f"Error: Invalid scenario '{scenario}'. Must be: crash, breakpoint, or memory")
        sys.exit(1)

    # Read transcript
    transcript_text = transcript_file.read_text()

    if not transcript_text.strip():
        print("Error: Transcript file is empty")
        sys.exit(1)

    # Verify MCP usage
    result = verify_transcript(transcript_text, scenario)

    # Print results
    print_results(result)

    # Output JSON for programmatic consumption
    json_output = json.dumps(result, indent=2)
    json_file = transcript_file.with_suffix('.verification.json')
    json_file.write_text(json_output)
    print(f"\nDetailed results saved to: {json_file}")

    # Exit with appropriate code
    sys.exit(0 if result['valid'] else 1)


if __name__ == "__main__":
    main()
