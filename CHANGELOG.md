# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-19

### Added
- **Dry-run mode**: Generate newsletter without sending (`--dry-run` flag)
- **Retry system**: Automatic retry with exponential backoff (3 attempts)
- **Status command**: View system status with `python main.py status`
- **Archive system**: Newsletters are automatically saved to `archives/` directory
- **Logging**: Structured logging with configurable level via `LOG_LEVEL` env var
- **CLI improvements**: Full argument parsing with `argparse`
- **Tests**: Unit tests for memory tools, content extraction, and Google Chat cards
- **CI/CD**: GitHub Actions workflow for automated testing
- **Dependabot**: Automatic dependency updates
- **DST support**: Dual cron schedules for winter/summer time

### Changed
- **Unified tool memory**: Merged `tools_memory_tool.py` and `tool_memory_tool.py` into single `tool_memory.py`
- **Robust memory tools**: Added JSON error handling, backup creation, and atomic writes
- **Pre-compiled regex**: Improved performance with pre-compiled regex patterns
- **Agent configuration**: Centralized in `AGENT_CONFIG` dict with reduced `max_iter` and timeouts
- **Webhook validation**: Added URL validation before sending
- **Fallback content**: Real tech facts instead of jokes

### Fixed
- **Bug 1.1**: Tool memory confusion between name-based and URL-based checking
- **Bug 1.2**: Fallback joke replaced with real historical tech fact
- **Bug 1.3**: Added try-except around crew execution with retry logic
- **Bug 1.4**: JSON corruption handling with backup creation
- **Bug 2.1**: DST issue with dual cron schedules

### Removed
- `tools_memory_tool.py` (merged into `tool_memory.py`)
- `tool_memory_tool.py` (merged into `tool_memory.py`)
- `custom_tool.py` (unused template)

### Security
- Webhook URL validation
- Minimal GitHub Actions permissions
- No sensitive data in console output
- Dependabot for security updates

## [1.1.0] - 2026-01-15

### Added
- Anti-duplicate memory system for tools and facts
- Newsletter restricted to weekdays only
- Title truncation for long news titles

### Changed
- Improved article quality criteria
- Enhanced tool selection guidelines

## [1.0.0] - 2026-01-01

### Added
- Initial release
- Four AI agents: news researcher, tool scout, fact finder, newsletter editor
- Google Chat integration via webhook
- Memory system for news URLs
- GitHub Actions for daily automation
