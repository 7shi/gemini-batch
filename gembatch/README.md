# Gembatch Package

This package provides command-line tools for managing Google Gemini batch jobs efficiently.

## Package Structure

### Core Modules

#### `main.py` - [Documentation](main.md)
**Primary CLI entry point with subcommand support**

- Unified command-line interface for all batch operations
- Global argument handling (`--job-info`)
- Centralized API key validation and client initialization
- Subcommand routing for submit/poll/cleanup operations

#### `submit.py` - [Documentation](submit.md)
**Batch job submission functionality**

- Multi-file batch processing with duplicate detection
- Configurable model selection via `-m`/`--model` parameter
- JSONL-based job tracking with comprehensive metadata
- Atomic error handling with automatic cleanup
- Progress reporting for bulk operations

#### `poll.py` - [Documentation](poll.md)
**Job monitoring and result retrieval**

- Real-time TUI monitoring with Rich library
- Automatic result download and systematic file organization
- Interrupt-safe state management with atomic updates
- Comprehensive job state tracking (success/failure/cancellation)
- Automatic resource cleanup to prevent quota bloat

#### `cleanup.py` - [Documentation](cleanup.md)
**Resource cleanup and management**

- Comprehensive batch resource discovery (files and jobs)
- Safe deletion with confirmation prompts
- Automation support via `--yes` flag
- Error-resilient cleanup with individual resource handling

#### `batch_info.py` - [Documentation](batch_info.md)
**Batch job data serialization and format conversion**

- Structured batch object serialization via `batch_to_dict()`
- Conversion from legacy flat format to new nested format
- Standardized job information schema across modules
- Standalone utility for batch data format migration

### Supporting Files

#### `__init__.py` - [Documentation](__init__.md)
**Package initialization and metadata**

- Dynamic version management from package metadata
- Controlled module exports through `__all__`
- Clean package interface for programmatic usage

## Architecture Overview

The package follows a modular design with clear separation of concerns:

- **main.py**: Handles CLI parsing and coordinates between modules
- **submit.py**: Focuses on job creation and submission logic
- **poll.py**: Manages job monitoring and result retrieval
- **cleanup.py**: Handles batch resource cleanup and management
- **batch_info.py**: Provides batch data serialization and format standardization
- **__init__.py**: Provides package-level configuration

All modules are designed to work together through the unified CLI interface provided by `main.py`, while maintaining independence for testing and maintenance purposes.

## Usage

This package is designed to be used through the main CLI entry point:

```bash
gembatch --job-info custom.jsonl submit -m gemini-2.0-flash *.jsonl
gembatch --job-info custom.jsonl poll
gembatch cleanup --yes
```

For detailed usage instructions, see the main [README.md](../README.md) in the project root.

## Documentation Philosophy

Each module includes detailed implementation rationale documentation (`.md` files) explaining **why** specific design decisions were made, rather than **how** the code works. This approach ensures long-term maintainability and helps future developers understand the reasoning behind architectural choices.