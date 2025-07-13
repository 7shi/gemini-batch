# CLI Entry Point Module

## Why This Implementation Exists

### Unified Entry Point Architecture
**Problem**: Multiple independent scripts (submit_batch.py, poll_batch.py) required users to remember different command names and manage separate configurations, leading to confusion and inconsistent usage patterns.

**Solution**: Implemented a single CLI entry point with subcommands (`gembatch submit`, `gembatch poll`, `gembatch cleanup`) to provide a cohesive user experience and centralized configuration management.

### Centralized API Client Management
**Problem**: Each module independently handled GEMINI_API_KEY validation and client initialization, creating code duplication and inconsistent error handling across commands.

**Solution**: Moved API key validation and client initialization to the main entry point, ensuring consistent error messages and eliminating redundant initialization code in submodules.

### Global Configuration Strategy
**Problem**: The `--job-info` parameter was needed by both submit and poll commands, but implementing it as separate subcommand options would require users to specify it twice for related operations.

**Solution**: Implemented `--job-info` as a global argument that applies to all subcommands, allowing users to set it once for the entire workflow while maintaining consistent job tracking across operations.

### Subcommand Parameter Isolation
**Problem**: Submit-specific options like `--model` should not be available or confusing when running poll operations, but a flat argument structure would mix unrelated options.

**Solution**: Used argparse subparsers to isolate command-specific arguments while preserving global options, providing clear command boundaries and preventing invalid option combinations.

### Resource Management Integration
**Problem**: Users needed a separate cleanup utility to manage Gemini batch resources, but running it as an independent script created inconsistent API client configuration and authentication patterns.

**Solution**: Integrated cleanup functionality as a subcommand (`gembatch cleanup`) to leverage the same API client initialization and error handling infrastructure, while providing optional `--yes` flag for automation scenarios.