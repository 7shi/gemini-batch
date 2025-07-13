# Gemini Batch Tools

Command-line tools for managing Google Gemini batch jobs efficiently.

For more information about Gemini Batch Mode, see the official documentation.

- [Batch Mode | Gemini API | Google AI for Developers](https://ai.google.dev/gemini-api/docs/batch-mode).

## Features

- **Job Management**: Complete lifecycle management from submission to result retrieval
- **Submit**: Upload JSONL files and create Gemini batch jobs with model selection
- **Poll**: Monitor job progress with real-time TUI and auto-download results
- **Resume**: Interrupt-safe job tracking with persistent state
- **Cleanup**: Automatic resource cleanup to prevent quota bloat
- **Flexible**: Global `--job-info` option for custom job tracking files

### Real-time Monitoring

The `poll` command provides a live TUI showing:

```text
╭────────────────────────────────────────── Gemini Batch Job Monitor ───────────────────────────────────────────╮
│ Last update: 2025-07-13 16:17:38                                                                              │
│                                                                                                               │
│                                              Batch Job Monitor                                                │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓ │
│ ┃ Input File                       ┃ Count ┃ State   ┃ Create Time         ┃ End Time            ┃ Duration ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩ │
│ │ examples/basic.jsonl             │     5 │ Success │ 2025-07-13 04:20:32 │ 2025-07-13 04:25:12 │ 4m 39s   │ │
│ │ examples/structured-output.jsonl │     5 │ Running │ 2025-07-13 04:20:35 │                     │          │ │
│ └──────────────────────────────────┴───────┴─────────┴─────────────────────┴─────────────────────┴──────────┘ │
│                                                                                                               │
│ Total jobs: 2 | Completed: 1 | Remaining: 1 | Next poll: 5s                                                   │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Monitoring can be safely interrupted and resumed:

1. **Submit** jobs: Creates persistent `job-info.jsonl` file
2. **Interrupt** polling: Ctrl+C safely exits
3. **Resume** polling: Run `gembatch poll` again - only incomplete jobs are monitored

## Requirements

- Python 3.10 or higher
- Dependencies: google-genai, rich
- Google Gemini API key (Tier 1 or higher)

```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Installation

### As a tool (recommended)

```bash
# Install as a tool
uv tool install https://github.com/7shi/gemini-batch.git

# Add ~/.local/bin to PATH if not already added
export PATH="$HOME/.local/bin:$PATH"
```

### From source

```bash
# Source installation with uv
git clone https://github.com/7shi/gemini-batch.git
cd gemini-batch
uv sync
```

**Note**: When using source installation, prefix all commands with `uv run` (e.g., `uv run gembatch`).

## Usage

### Basic Workflow

```bash
# 1. Submit multiple files (job info saved to `job-info.jsonl`)
gembatch submit batch1.jsonl batch2.jsonl batch3.jsonl

# 2. Monitor progress (live TUI)
gembatch poll

# 3. Results automatically saved to results/ directory
ls results/
# batch1.jsonl  batch2.jsonl  batch3.jsonl
```

### Submit Batch Jobs

Submit one or more JSONL files as batch jobs:

```bash
gembatch submit file1.jsonl file2.jsonl file3.jsonl
```

With custom model:
```bash
gembatch submit -m gemini-2.0-flash-thinking-exp file1.jsonl
```

Job info is saved to `job-info.jsonl` by default, but you can use a custom file:
```bash
gembatch --job-info my-jobs.jsonl submit *.jsonl
```

### Monitor Jobs

Monitor all jobs with real-time status display:

```bash
gembatch poll
```

Monitor specific job file:
```bash
gembatch --job-info my-jobs.jsonl poll
```

### Cleanup Resources

Clean up Gemini batch resources (files and batch jobs) to prevent quota bloat. This tool addresses file deletion issues that existed in v0.3.1 and earlier versions:

```bash
gembatch cleanup
```

Skip confirmation prompt:
```bash
gembatch cleanup -y
```

**Note**: Currently, the Batch Job List API may not detect existing jobs properly, but this will be addressed in future updates.

## File Structure

```
your-project/
├── input1.jsonl              # Input files
├── input2.jsonl
├── job-info.jsonl            # Job tracking (auto-generated)
└── results/                  # Downloaded results
    ├── input1.jsonl
    └── input2.jsonl
```

## Job Info Format

The `job-info.jsonl` file tracks job status using structured batch objects. For more details, see [batch_info.md](gembatch/batch_info.md):

```json
{"input_file": "input1.jsonl", "count": 5, "uploaded_file_name": "files/...", "batch": {"name": "batches/...", "state": "JOB_STATE_PENDING", "create_time": "2024-01-01T12:00:00+00:00", "model": "models/gemini-2.5-flash-lite-preview-06-17"}}
{"input_file": "input2.jsonl", "count": 3, "uploaded_file_name": "files/...", "batch": {"name": "batches/...", "state": "JOB_STATE_SUCCEEDED", "create_time": "2024-01-01T12:01:00+00:00", "end_time": "2024-01-01T12:30:00+00:00", "model": "models/gemini-2.5-flash-lite-preview-06-17", "dest": {"file_name": "files/batch-..."}}}
```
