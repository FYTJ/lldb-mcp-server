# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-27

### Added
- **40 MCP tools** for comprehensive debugging capabilities:
  - Session management (3 tools)
  - Target control (6 tools)
  - Breakpoints (4 tools)
  - Execution control (5 tools)
  - Inspection (6 tools)
  - Memory operations (2 tools)
  - Watchpoints (3 tools)
  - Registers (2 tools)
  - Symbols & modules (2 tools)
  - Advanced tools (4 tools)
  - Security analysis (2 tools)
  - Core dumps (2 tools)
- **Multi-session architecture** with isolated debugging sessions
- **Event-driven system** with background event collection and polling
- **Security analysis** features (crash exploitability, suspicious function detection)
- **Session transcripts** with automatic logging
- **Homebrew LLVM support** for Python 3.10+ compatibility
- **uvx deployment** for simplified installation from PyPI

### Changed
- **Simplified to stdio-only transport** (removed HTTP/SSE support)
- **Production-ready structure** (removed development tests and scripts)
- **Streamlined documentation** focused on end-user deployment
- **Updated README** with comprehensive English documentation and Chinese translation

### Removed
- HTTP and SSE transport modes (stdio only)
- Development test suites (`tests/` directory)
- Helper scripts (`scripts/` directory)
- HTTP-related code and dependencies
- Development documentation from public release

### Fixed
- LLDB Python binding compatibility across Python 3.10-3.13
- Memory read API compatibility across LLDB versions
- Watchpoint size reporting for different LLDB versions
- Environment variable handling for LLDB path detection

## [0.1.0] - Initial Development

### Added
- Initial LLDB MCP server implementation
- FastMCP integration
- Basic debugging tools
- HTTP transport support (development mode)

---

For more details, see [GitHub Releases](https://github.com/FYTJ/lldb-mcp-server/releases).
