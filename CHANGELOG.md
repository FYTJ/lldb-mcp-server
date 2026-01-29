# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-29

### Added
- **Linux platform support** - Now supports Ubuntu 22.04+, Fedora 38+, and Arch Linux in addition to macOS
- **Platform abstraction layer** - New `platform/` package with pluggable platform providers:
  - `platform/detector.py` - Automatic OS and Linux distribution detection
  - `platform/provider.py` - Abstract platform provider interface and factory
  - `platform/macos.py` - macOS-specific LLDB path discovery (Homebrew and Xcode)
  - `platform/linux.py` - Linux-specific LLDB path discovery (Ubuntu, Fedora, Arch)
- **Automatic platform detection** - Detects OS, Linux distribution, and architecture automatically
- **Distribution-specific path discovery** - Comprehensive LLDB Python binding search for different Linux distributions
- **Linux diagnostic script** - `scripts/diagnose_lldb_linux.sh` for troubleshooting LLDB setup on Linux
- **Structured documentation** - Split README into separate focused documents:
  - `docs/FEATURES.md` / `docs/FEATURES.zh.md` - Complete list of 40 tools
  - `docs/CONFIGURATION.md` / `docs/CONFIGURATION.zh.md` - Detailed IDE configuration
  - `docs/USAGE.md` / `docs/USAGE.zh.md` - Usage examples and skill integration
  - `docs/TROUBLESHOOTING.md` / `docs/TROUBLESHOOTING.zh.md` - Platform-specific troubleshooting
  - `docs/LINUX_INSTALLATION.md` - Comprehensive Linux installation guide
- **Enhanced configuration system** - Added `platform_override` and `platform_configs` to config schema

### Changed
- **Refactored LLDB environment setup** - `ensure_lldb_env()` now uses platform providers instead of hardcoded paths
- **Improved LLDB path detection** - Platform-aware search covering:
  - macOS: Homebrew LLVM (Intel and Apple Silicon), Xcode Command Line Tools
  - Ubuntu/Debian: `/usr/lib/llvm-{version}/lib/python{version}/site-packages`
  - Fedora/RHEL: `/usr/lib64/llvm{version}/lib/python{version}/site-packages`
  - Arch Linux: `/usr/lib/python{version}/site-packages`
- **Streamlined README** - Reduced from 800+ lines to ~270 lines, focusing on quick start
- **Reorganized documentation** - Better information architecture with clear separation of concerns
- **Enhanced Linux installation instructions** - Added warnings about uvx incompatibility on Linux

### Fixed
- **Linux LLDB import issues** - Added proper handling of `LLDB_PYTHON_PATH` for isolated environments
- **Cross-platform environment variables** - Correct use of `LD_LIBRARY_PATH` (Linux) vs `DYLD_LIBRARY_PATH` (macOS)
- **Library preloading** - Platform-specific handling of `liblldb.so` (Linux) vs `LLDB.framework` (macOS)

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
