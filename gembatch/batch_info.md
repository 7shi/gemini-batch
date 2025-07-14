# Batch Info Module

This document explains the `batch_info.py` module, which provides utilities for processing Google Gemini batch job information and atomic file operations for concurrent access.

The module includes:
- Job information conversion utilities
- Atomic file operations for safe concurrent access
- Backward compatibility support for legacy formats

Command line usage requires:
- The `GEMINI_API_KEY` environment variable to be set for authentication
- A required command line argument specifying the input JSONL file path

## Development Log

### Initial API Exploration

The development began with interactive Python session to understand the batch API structure:

```python
>>> import sys, os, json
>>> from google import genai
>>> client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"api_version": "v1alpha"})
>>> client.batches.list()
<google.genai.pagers.Pager object at 0x7ce61c59d400>
>>> list(client.batches.list())
[]
>>> b=client.batches.get(name="batches/...")
>>> b
BatchJob(
  create_time=datetime.datetime(2025, 7, 12, 16, 1, 38, 750979, tzinfo=TzInfo(UTC)),
  dest=BatchJobDestination(
    file_name='files/batch-...'
  ),
  display_name='batch-job-batch_requests',
  end_time=datetime.datetime(2025, 7, 12, 16, 2, 35, 523435, tzinfo=TzInfo(UTC)),
  model='models/gemini-2.5-flash-lite-preview-06-17',
  name='batches/...',
  state=<JobState.JOB_STATE_SUCCEEDED: 'JOB_STATE_SUCCEEDED'>,
  update_time=datetime.datetime(2025, 7, 12, 16, 3, 5, 823235, tzinfo=TzInfo(UTC))
)
>>> b.create_time
datetime.datetime(2025, 7, 12, 16, 1, 38, 750979, tzinfo=TzInfo(UTC))
>>> b.end_time
datetime.datetime(2025, 7, 12, 16, 2, 35, 523435, tzinfo=TzInfo(UTC))
```

### Module Components

## Utility Functions

### `batch_to_dict(batch_job)`

Converts a BatchJob object to a dictionary with the following fields:
- `name`: Batch job identifier
- `display_name`: Human-readable name
- `model`: Model used for the batch
- `state`: Current job state (e.g., "JOB_STATE_SUCCEEDED")
- `create_time`: Job creation timestamp (ISO format)
- `update_time`: Last update timestamp (ISO format)
- `end_time`: Job completion timestamp (ISO format)
- `dest`: Destination file information (if available)

### `get_batch_info(client, batch_name)`

Retrieves batch job information using the Gemini client and returns it as a dictionary.

### `count_lines(filename)`

Counts non-empty lines in a file to determine the number of queries.

### `convert_job_if_needed(client, job_info)`

Core conversion function that serves as a backward compatibility trick:
- Returns `None` if job_info is already in the correct format (has batch field and count)
- Adds missing count field if batch exists but count is missing/zero
- Preserves `uploaded_file_name` field during conversion to maintain source file cleanup capability
- Converts legacy format to new format by fetching batch info from API
- This function enables seamless migration from v0.1.0 format without breaking existing workflows

## AtomicJobManager Class

The `AtomicJobManager` class provides thread-safe operations for managing job information files, solving race conditions that occur when multiple processes (submit and poll) access the same file simultaneously.

For detailed background on the race condition discovery, solution evaluation, and implementation rationale, see [Atomic Job Manager Implementation](../docs/20250714-atomic-operations.md).

### Class Methods

#### `__init__(self, job_info_file, client=None, timeout=30, retry_interval=1, read_only=False)`
Initialize the manager with file path, optional client for conversions, timeout settings, and read-only mode flag.

#### Context Management
- `__enter__(self)` and `__exit__(self, exc_type, exc_val, exc_tb)`: Handle lock acquisition and release with automatic cleanup

#### File Operations
- `file_exists(self, filepath)`: Check if a file exists (utility method for submit operations)
- `get_all_jobs(self)`: Get copy of all jobs for display purposes
- `was_converted(self)`: Check if any job conversion occurred during loading

#### Job Management
- `find_job_by_input_file(self, filename)`: Find existing job by input file name (for duplicate detection)
- `find_job_by_batch_name(self, batch_name)`: Find existing job by batch name (for status updates)
- `add_job(self, job_record)`: Add new job if not exists, return True if added, False if already exists (raises `RuntimeError` if called in read-only mode)
- `update_job_by_batch_name(self, job_record)`: Update job by extracting batch name from job record, return True if updated, False if not found (raises `RuntimeError` if called in read-only mode)
- `bulk_update_jobs(self, job_list)`: Update multiple jobs efficiently (raises `RuntimeError` if called in read-only mode)

## Command Line Interface

### `main()`

Main processing loop (for backward compatibility command line usage):
1. Parses command line arguments to get input file path
2. Initializes the Gemini client
3. Uses `AtomicJobManager` with `read_only=True` for safe file reading with automatic conversion
4. Outputs converted job data in JSONL format outside the lock for optimal performance

## Implementation Design

### Atomic File Operations
The module uses a temporary file strategy for atomic operations. For detailed technical implementation and design decisions, see [Atomic Job Manager Implementation](../docs/20250714-atomic-operations.md).

#### Read-Only Mode
For read-only operations (like the command line interface), the module can be used in read-only mode:
- Set `read_only=True` when initializing `AtomicJobManager`
- `AtomicJobManager` still acquires locks for safe reading
- File updates are automatically prevented regardless of conversion results
- Update methods (`add_job`, `update_job_by_batch_name`, `bulk_update_jobs`) raise `RuntimeError` when called
- Data processing and output occur outside the lock to minimize lock time
- This ensures consistency even when other processes are modifying the file

### Backward Compatibility
The module maintains compatibility with legacy job formats through automatic detection and conversion, enabling seamless migration from v0.1.0 format without breaking existing workflows.

### Usage

The script supports two modes of operation:

1. **Legacy mode** (for v0.1.0 format conversion):
```bash
uv run batch_info.py job-info.jsonl
```

2. **Passthrough mode** (when input already contains batch data):
```bash
uv run batch_info.py processed-data.jsonl
```

### Input Format

The script automatically detects the input format and switches behavior:

#### Legacy Format (v0.1.0)
For legacy mode, the script expects entries like:

```json
{
  "input_file": "1-simple/batch_requests.jsonl",
  "job_name": "batches/...",
  "uploaded_file_name": "files/...",
  "display_name": "batch-job-batch_requests",
  "created_at": "2025-07-13T01:01:38.807581",
  "completed_at": "2025-07-13T01:03:03.448724",
  "final_state": "JOB_STATE_SUCCEEDED",
  "duration_seconds": 84
}
```

#### Passthrough Mode
For passthrough mode, the input should match the output format. If `count` is missing or zero, it will be calculated from the input file.

### Output Format

The script outputs JSONL with the following structure (formatted):

```json
{
  "input_file": "1-simple/batch_requests.jsonl",
  "count": 5,
  "uploaded_file_name": "files/...",
  "batch": {
    "name": "batches/...",
    "display_name": "batch-job-batch_requests",
    "model": "models/gemini-2.5-flash-lite-preview-06-17",
    "state": "JOB_STATE_SUCCEEDED",
    "create_time": "2025-07-12T16:01:38.750979+00:00",
    "update_time": "2025-07-12T16:03:05.823235+00:00",
    "end_time": "2025-07-12T16:02:35.523435+00:00",
    "dest": {
      "file_name": "files/batch-..."
    }
  }
}
```

The `count` field represents the number of queries (non-empty lines) in the input file.
The `uploaded_file_name` field stores the source file identifier for cleanup operations.
