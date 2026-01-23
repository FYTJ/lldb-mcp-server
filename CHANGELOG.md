# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - Unreleased

### Added
- FastMCP server with HTTP compatibility routes (`/tools/list`, `/tools/call`).
- Expanded tool coverage across registers, symbol search, module listing, core dumps, and crash analysis.
- Pytest suite covering sessions, targets, breakpoints, execution, inspection, memory, watchpoints, advanced tools, security, and integration flows.
- LLDB environment helper script and expanded configuration via `config.json`.

### Changed
- Documentation updated with Homebrew LLVM + Python 3.13 setup guidance.

### Fixed
- LLDB API compatibility for memory reads and watchpoint size reporting across versions.
