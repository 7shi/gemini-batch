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

### Rich TUI Fixed-position Display with Manual Refresh Control
**Problem**: Traditional log output format during long-term polling of 23 jobs creates continuous log flow making current status difficult to grasp, requiring scrolling to check past information.

**Solution**: Implemented TUI-like fixed-position display using `rich.live.Live` with manual refresh control. The implementation uses `auto_refresh=False` to prevent automatic screen updates during sleep intervals, ensuring updates occur only when explicitly triggered by `live.update()` and `live.refresh()` calls. This eliminates unnecessary redraws during countdown timers and provides precise control over when the display refreshes. The UI features a bordered panel with job status table and summary information positioned to minimize screen flicker during updates. Individual job rows are highlighted with red background during status checks for immediate visual feedback. To reduce display flicker during countdown updates, the countdown interval was optimized from 1-second to 5-second intervals, reducing update frequency from 30 times to 6 times per polling cycle. Detailed optimization techniques are documented in [Rich Library Refresh Optimization Guide](../docs/20250713-rich-refresh.md).

### Comprehensive Job State Management
**Problem**: Managing only successful jobs would leave failure and cancellation status unclear, making operational problem analysis and re-execution decisions difficult.

**Solution**: Update batch object with complete job information for all termination states (success/failure/cancellation) using `batch_to_dict()`. TUI display extracts state information from `batch.state` and color-codes states (✓ success=green, ✗ failure=red, ⊘ cancellation=orange) for comprehensive management of all job situations.

### Automatic Processing Time Calculation and Recording
**Problem**: Understanding each job's processing time for batch processing performance analysis and operational planning is desired, but manual time measurement is difficult and inaccurate.

**Solution**: Automatically calculate duration from `batch.create_time` and `batch.end_time` extracted from the structured batch object. TUI display shows in readable "3h 45m 30s" format, enabling processing performance analysis and future processing time prediction.

### Automated Resource Cleanup for Operational Load Reduction
**Problem**: When Gemini API batch jobs remain after job completion, API quota pressure and increased management overhead create operational burden.

**Solution**: Automatically delete batch jobs through `cleanup_job_resources` function upon job completion (regardless of success/failure/cancellation). Job names are extracted from `batch.name` in the structured batch object. Incorporated safe deletion processing that continues even when exceptions occur, eliminating need for manual cleanup work by operators.

### Complete Resource Cleanup Discovery and Implementation
**Problem**: The original cleanup implementation only deleted batch jobs but left uploaded source files (src) in the cloud, discovered when implementing the standalone cleanup functionality that revealed orphaned files accumulating in the system.

**Solution**: Enhanced `cleanup_job_resources` to delete both source files and batch jobs, while preserving result files (`batch_job.dest.file_name`) that users have already downloaded. Since batch objects don't contain source file information (src field is not available in Gemini API), the implementation now uses the `uploaded_file_name` field stored in job records during submission. The function receives the complete `job` object to access both `uploaded_file_name` for source file cleanup and `batch.name` for batch job deletion. Each deletion operation is wrapped in individual try-catch blocks to ensure cleanup continues even if specific resources fail to delete.

### Backward Compatibility Through Automatic Format Conversion
**Problem**: As the project evolved, job-info.jsonl files existed in both legacy format (v0.1.0 with job_name field) and new format (with batch field and count). Users needed seamless polling regardless of format without manual conversion steps.

**Solution**: Integrated `convert_job_if_needed` from batch_info module as a backward compatibility trick to automatically detect and convert legacy format entries during file loading. The conversion is performed transparently and the updated file is automatically saved, ensuring all subsequent operations use the consistent new format. This compatibility layer eliminates breaking changes for users with existing legacy format files.

### Code Simplification Through Unnecessary Tracking Removal
**Problem**: The original implementation tracked line numbers (`_line_num`) for each job record, adding complexity to data handling without providing functional value since the tracking data was only excluded during file writing.

**Solution**: Removed `_line_num` tracking entirely from `load_jobs_from_file` and `write_updated_jobs` functions. This simplification eliminates unnecessary data manipulation and reduces memory overhead without affecting core functionality, as job identification is handled through batch names rather than line positions.

### Enhanced Progress Display with Query Count Visibility
**Problem**: When monitoring multiple batch jobs, operators needed to quickly assess the scale of each job (number of queries) to understand processing load and estimate completion times, but this information was not visible in the monitoring interface.

**Solution**: Added Count column to the TUI display showing the number of queries in each input file. The count is displayed with comma separators for readability (e.g., "1,000") and right-aligned for easy visual comparison. This enhancement provides immediate visibility into job scale and helps operators prioritize attention during monitoring.

### Source File Information Preservation for Reliable Cleanup
**Problem**: Batch objects returned by the Gemini API don't contain source file information (src field is not available), making it impossible to clean up uploaded source files during job completion, leading to orphaned files accumulating in the system.

**Solution**: Modified submit process to store `uploaded_file_name` field in job records during submission, preserving the source file identifier for later cleanup operations. Updated `cleanup_job_resources` function to accept complete job objects and use the stored `uploaded_file_name` for source file deletion. This approach ensures reliable cleanup regardless of API limitations while maintaining backward compatibility through the `convert_job_if_needed` function that preserves existing `uploaded_file_name` fields during format conversion.