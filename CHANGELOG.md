# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2025-07-13

### Added
- Count field display in poll TUI showing number of queries per job with comma separators and right alignment

### Changed
- Automatic format conversion for backward compatibility with v0.1.0 `job-info.jsonl` files

## [0.3.0] - 2025-07-13

### Added
- New `gembatch cleanup` subcommand for comprehensive resource management

### Fixed
- Resource deletion in poll module now properly removes source files
- Display flicker during countdown by changing intervals to 5 seconds (Rich library limitations prevent complete elimination)

## [0.2.1] - 2025-07-13

### Fixed
- Rich Live display refresh control to prevent unnecessary updates during sleep intervals
- Manual refresh control with `auto_refresh=False` for precise update timing

## [0.2.0] - 2025-07-13

### Added
- Comprehensive example files with basic and structured output samples

### Changed
- **Breaking**: Migrated to new structured batch format with nested batch objects

### Improved
- Job monitoring display with red background highlighting for active checks
- Optimized Rich UI rendering for reduced flickering during job monitoring

## [0.1.0] - 2025-07-13

### Added
- Initial release with CLI interface (`gembatch submit` and `gembatch poll`)
- Multi-file batch job submission with model selection
- Real-time TUI monitoring with job status and progress display
- Interrupt-safe job tracking and resume capability
- Automatic resource cleanup to prevent quota bloat
