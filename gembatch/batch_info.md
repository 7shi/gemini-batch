# Batch Info Script

This document explains the `batch_info.py` script, which is designed to retrieve and process Google Gemini batch job information.

## Background

The script was developed based on interactive exploration of the Google Gemini batch API. The development process involved understanding the structure of batch job objects and determining how to convert them to a more usable dictionary format.

## Usage

```bash
uv run batch_info.py <input_file>
```

For example:
```bash
uv run batch_info.py job-info.jsonl
```

The script requires:
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

### Script Components

## Functions

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

### `main()`

Main function that:
1. Parses command line arguments to get input file path
2. Initializes the Gemini client
3. Reads job information from the specified JSONL file
4. For each job, retrieves detailed batch information
5. Outputs combined data in JSONL format

## Input Format

The script expects a JSONL file with entries like:

```json
{"input_file": "1-simple/batch_requests.jsonl", "job_name": "batches/...", "uploaded_file_name": "files/...", "display_name": "batch-job-batch_requests", "created_at": "2025-07-13T01:01:38.807581", "completed_at": "2025-07-13T01:03:03.448724", "final_state": "JOB_STATE_SUCCEEDED", "duration_seconds": 84}
```

## Output Format

The script outputs JSONL with the following structure:

```json
{
  "input_file": "1-simple/batch_requests.jsonl",
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
