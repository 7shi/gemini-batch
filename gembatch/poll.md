# Batch Job Polling and Results Module

## Why This Implementation Exists

### Automated Multi-job Polling Management
**Problem**: After submitting 23 batch jobs with submit_batch.py, manually checking each job's completion status and individually downloading results is inefficient and prone to oversight.

**Solution**: Implemented automatic polling of all jobs in job-info.jsonl with automatic result download for completed jobs. Centralized monitoring and result retrieval through `gembatch poll` for comprehensive job management.

### Integration with JSONL Job Management
**Problem**: A polling system compatible with submit_batch.py's JSONL format job management was needed, but reference implementation only supported single job JSON format.

**Solution**: Implemented mechanism to read each line of job-info.jsonl individually and determine completion status by `batch.state` field in the structured batch object, supporting concurrent management of multiple jobs.

### Safe JSONL File Update Functionality
**Problem**: Directly updating job-info.jsonl upon job completion risks file corruption due to interruption or exceptions during writing, with concerns about race conditions during concurrent execution.

**Solution**: Implemented atomic operation of write to temporary file → delete original file → rename using `tempfile.NamedTemporaryFile` for safe update processing, preventing file corruption.

### Systematic Result File Storage
**Problem**: A systematic approach for saving each job's result files to appropriate locations was needed, while avoiding filename conflicts and location confusion.

**Solution**: Adopted `batch/results/original-filename.jsonl` naming convention, creating results/ subdirectory within batch directory and preserving original filenames for result storage. Results from batch/003.jsonl are saved to batch/results/003.jsonl.

### Error Handling and Continuity Assurance
**Problem**: If polling errors occur for one job, stopping overall monitoring would prevent result retrieval for other normal jobs.

**Solution**: Wrapped each job's polling in individual try-catch blocks, designed to continue processing other jobs even when errors occur. Error content is displayed but overall monitoring continues with safe implementation.

### Operational Visibility Through Progress Display
**Problem**: When polling 23 jobs for extended periods, unclear progress status and job states prevent operators from understanding the situation.

**Solution**: Implemented detailed progress display with timestamps showing each job's state, newly completed count, remaining jobs, and countdown to next polling, achieving complete visibility of operational status.

### Interruption and Resume Support for Flexibility
**Problem**: When interruption becomes necessary during long polling operations, re-downloading results from already completed jobs wastes time and resources.

**Solution**: Through persistence of completion state via `batch.state` in the structured batch object, automatically detect only incomplete jobs during re-execution after script interruption. Already completed jobs are skipped for efficient processing resumption.

### Rich TUI Fixed-position Display with Optimized UI
**Problem**: Traditional log output format during long-term polling of 23 jobs creates continuous log flow making current status difficult to grasp, requiring scrolling to check past information.

**Solution**: Implemented TUI-like fixed-position display using `rich.live.Live` with optimized UI layout. The current implementation features a bordered panel containing the job status table, with summary information and countdown timer positioned below the table to minimize screen flicker. During status checks, individual job rows are highlighted with red background for immediate visual feedback. Removed `refresh_per_second` parameter to enable immediate rendering instead of delayed periodic updates, ensuring real-time responsiveness during status checking operations. Detailed optimization techniques are documented in [Rich Library Refresh Optimization Guide](../docs/20250713-rich-refresh.md).

### Comprehensive Job State Management
**Problem**: Managing only successful jobs would leave failure and cancellation status unclear, making operational problem analysis and re-execution decisions difficult.

**Solution**: Update batch object with complete job information for all termination states (success/failure/cancellation) using `batch_to_dict()`. TUI display extracts state information from `batch.state` and color-codes states (✓ success=green, ✗ failure=red, ⊘ cancellation=orange) for comprehensive management of all job situations.

### Automatic Processing Time Calculation and Recording
**Problem**: Understanding each job's processing time for batch processing performance analysis and operational planning is desired, but manual time measurement is difficult and inaccurate.

**Solution**: Automatically calculate duration from `batch.create_time` and `batch.end_time` extracted from the structured batch object. TUI display shows in readable "3h 45m 30s" format, enabling processing performance analysis and future processing time prediction.

### Automated Resource Cleanup for Operational Load Reduction
**Problem**: When Gemini API batch jobs remain after job completion, API quota pressure and increased management overhead create operational burden.

**Solution**: Automatically delete batch jobs through `cleanup_job_resources` function upon job completion (regardless of success/failure/cancellation). Job names are extracted from `batch.name` in the structured batch object. Incorporated safe deletion processing that continues even when exceptions occur, eliminating need for manual cleanup work by operators.