# Gemini Batch Tools

Command-line tools for managing Google Gemini batch jobs efficiently.

For more information about Gemini Batch Mode, see the official documentation.

- [Batch Mode | Gemini API | Google AI for Developers](https://ai.google.dev/gemini-api/docs/batch-mode).

## Features

- **Submit**: Upload JSONL files and create Gemini batch jobs with model selection
- **Poll**: Monitor job progress with real-time TUI and auto-download results
- **Resume**: Interrupt-safe job tracking with persistent state
- **Cleanup**: Automatic resource cleanup to prevent quota bloat
- **Flexible**: Global `--job-info` option for custom job tracking files

### Real-time Monitoring

The `poll` command provides a live TUI showing:

- ✓ Job status (Success/Failed/Cancelled/Running)
- ⏱️ Creation and completion times
- ⏳ Duration for completed jobs
- 📊 Progress summary
- ⏰ Countdown to next poll

### Resume Support

Jobs can be safely interrupted and resumed:

1. **Submit** jobs: Creates persistent job-info.jsonl
2. **Interrupt** polling: Ctrl+C safely exits
3. **Resume** polling: Run `gembatch poll` again - only incomplete jobs are monitored

## Requirements

- Python 3.10 or higher
- Dependencies: `google-genai`, `rich`
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

### Submit Batch Jobs

Submit one or more JSONL files as batch jobs:

```bash
gembatch submit file1.jsonl file2.jsonl file3.jsonl
```

With custom model:
```bash
gembatch submit -m gemini-2.0-flash-thinking-exp file1.jsonl
```

With custom job info file:
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

The `job-info.jsonl` file tracks job status:

```text
{\"input_file\": \"input1.jsonl\", \"job_name\": \"projects/.../batches/...\", \"created_at\": \"2024-01-01T12:00:00\"}
{\"input_file\": \"input2.jsonl\", \"job_name\": \"projects/.../batches/...\", \"created_at\": \"2024-01-01T12:01:00\", \"completed_at\": \"2024-01-01T12:30:00\", \"final_state\": \"JOB_STATE_SUCCEEDED\", \"duration_seconds\": 1740}
```

## Examples

### Basic Workflow

```bash
# 1. Submit multiple files
gembatch submit batch1.jsonl batch2.jsonl batch3.jsonl

# 2. Monitor progress (live TUI)
gembatch poll

# 3. Results automatically saved to results/ directory
ls results/
# batch1.jsonl  batch2.jsonl  batch3.jsonl
```

### Advanced Usage

```bash
# Submit with custom model
gembatch submit -m gemini-2.0-flash-thinking-exp *.jsonl

# Use custom job tracking file
gembatch --job-info production-jobs.jsonl submit *.jsonl
gembatch --job-info production-jobs.jsonl poll

# Combine options
gembatch --job-info custom.jsonl submit -m gemini-2.0-flash *.jsonl
```
