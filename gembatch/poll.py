#!/usr/bin/env python3
"""
Poll job-info.jsonl for batch job status and download results when completed
"""

import os
import json
import sys
import time
import argparse
import tempfile
from datetime import datetime
from pathlib import Path
from google import genai
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

POLL_INTERVAL = 30  # Poll every 30 seconds

console = Console()


def create_job_status_display(jobs, last_update, countdown=None):
    """Create a table display for job status"""
    table = Table(title="Batch Job Monitor")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Created", style="dim")
    table.add_column("Completed", style="green")
    table.add_column("Duration", style="yellow")
    
    completed_count = 0
    for job in jobs:
        input_file = job['input_file']
        
        if 'completed_at' in job:
            completed_count += 1
            final_state = job.get('final_state', '')
            if final_state == 'JOB_STATE_SUCCEEDED':
                status = "✓ Success"
                status_style = "green"
            elif final_state == 'JOB_STATE_FAILED':
                status = "✗ Failed"
                status_style = "red"
            elif final_state == 'JOB_STATE_CANCELLED':
                status = "⊘ Cancelled"
                status_style = "orange1"
            else:
                # For backward compatibility
                status = "✓ Completed"
                status_style = "green"
        else:
            status = "⏳ Running"
            status_style = "yellow"
        
        created_at = job.get('created_at', '')[:19].replace('T', ' ')
        completed_at = job.get('completed_at', '')[:19].replace('T', ' ') if 'completed_at' in job else ''
        
        # Duration display
        duration_display = ""
        if 'duration_seconds' in job:
            duration_sec = job['duration_seconds']
            hours = duration_sec // 3600
            minutes = (duration_sec % 3600) // 60
            seconds = duration_sec % 60
            if hours > 0:
                duration_display = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_display = f"{minutes}m {seconds}s"
            else:
                duration_display = f"{seconds}s"
        
        table.add_row(
            input_file,
            Text(status, style=status_style),
            created_at,
            completed_at,
            duration_display
        )
    
    # Summary information
    total_jobs = len(jobs)
    pending_jobs = total_jobs - completed_count
    
    summary = Text()
    summary.append(f"Total jobs: {total_jobs} | ", style="bold")
    summary.append(f"Completed: {completed_count} | ", style="green bold")
    summary.append(f"Remaining: {pending_jobs}", style="yellow bold")
    
    if countdown is not None:
        summary.append(f" | Next poll: {countdown}s", style="cyan")
    
    # Wrap in panel
    content = [
        Text(f"Last update: {last_update}", style="dim"),
        Text(""),
        summary,
        Text(""),
        table
    ]
    
    if pending_jobs == 0:
        content.append(Text(""))
        content.append(Text("🎉 All jobs completed!", style="green bold"))
    
    from rich.columns import Columns
    from rich.align import Align
    
    return Panel(
        Align.center(Columns(content, equal=True, expand=True)),
        title="Gemini Batch Job Monitor",
        border_style="blue"
    )


def load_jobs_from_file(job_info_file):
    """Load job information from JSONL file"""
    if not os.path.exists(job_info_file):
        print(f"Error: Job info file not found: {job_info_file}", file=sys.stderr)
        return []
    
    jobs = []
    try:
        with open(job_info_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        job_record = json.loads(line)
                        job_record['_line_num'] = line_num  # Record line number
                        jobs.append(job_record)
                    except json.JSONDecodeError as e:
                        print(f"Warning: JSON parse error at line {line_num}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error: Failed to load job info file: {e}", file=sys.stderr)
        return []
    
    return jobs


def get_pending_jobs(jobs):
    """Get list of incomplete jobs"""
    return [job for job in jobs if 'completed_at' not in job]


def update_job_completion(job_info_file, jobs, job_index, completed_at_datetime, final_state):
    """Add completion time, duration, and final state to specified job and update JSONL file"""
    # Add completion time and final state to the job
    jobs[job_index]['completed_at'] = completed_at_datetime.isoformat()
    jobs[job_index]['final_state'] = final_state
    
    # Calculate duration
    if 'created_at' in jobs[job_index]:
        try:
            created_time = datetime.fromisoformat(jobs[job_index]['created_at'])
            duration = completed_at_datetime - created_time
            jobs[job_index]['duration_seconds'] = int(duration.total_seconds())
        except Exception:
            # Skip if datetime parsing fails
            pass
    
    # Write new content to temporary file
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, 
                                       dir=os.path.dirname(job_info_file),
                                       prefix=f"{os.path.basename(job_info_file)}.tmp") as f:
            temp_file = f.name
            for job in jobs:
                # Exclude _line_num as it's for internal management
                job_data = {k: v for k, v in job.items() if k != '_line_num'}
                json.dump(job_data, f, ensure_ascii=False)
                f.write('\n')
        
        # Delete original file and rename temp file
        os.remove(job_info_file)
        os.rename(temp_file, job_info_file)
        
    except Exception as e:
        # Delete temp file on error
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        raise e


def cleanup_job_resources(client, job):
    """Clean up job and file resources"""
    job_name = job['job_name']
    input_file_name = job.get('uploaded_file_name')
    
    # Delete batch job
    try:
        client.batches.delete(name=job_name)
    except Exception:
        # Ignore errors (might already be deleted)
        pass
    
    # Delete input file
    if input_file_name:
        try:
            client.files.delete(name=input_file_name)
        except Exception:
            # Ignore errors (might already be deleted)
            pass


def download_job_results(client, job, input_file_path):
    """Download job results"""
    try:
        # Get latest job status
        batch_job = client.batches.get(name=job['job_name'])
        
        if batch_job.state.name != "JOB_STATE_SUCCEEDED":
            return False, f"Job not successful: {batch_job.state.name}"
        
        # Download result file
        result_file_name = batch_job.dest.file_name
        file_content_bytes = client.files.download(file=result_file_name)
        file_content = file_content_bytes.decode("utf-8")
        
        # Determine download destination (results/ under batch directory)
        input_path = Path(input_file_path)
        results_dir = input_path.parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Use input_path.name for filename
        output_file = results_dir / input_path.name
        
        # Save results
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(file_content)
        
        return True, str(output_file)
        
    except Exception as e:
        return False, f"Failed to download results: {e}"


def poll_jobs(job_info_file, client):
    """Poll jobs and process completed ones"""
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            # Load latest job information
            jobs = load_jobs_from_file(job_info_file)
            if not jobs:
                live.update(Text("Error: No jobs found", style="red bold"))
                break
            
            # Get incomplete jobs
            pending_jobs = get_pending_jobs(jobs)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if not pending_jobs:
                live.update(create_job_status_display(jobs, current_time))
                break
            
            # Update display
            live.update(create_job_status_display(jobs, current_time))
            
            # Check status of each incomplete job
            newly_completed = 0
            for i, job in enumerate(jobs):
                if 'completed_at' in job:
                    continue  # Already completed
                
                try:
                    batch_job = client.batches.get(name=job['job_name'])
                    current_state = batch_job.state.name
                    
                    if current_state != "JOB_STATE_PENDING":
                        # Job completed (success, failure, or cancellation)
                        completed_at = datetime.now()
                        
                        if current_state == "JOB_STATE_SUCCEEDED":
                            # Download results
                            success, message = download_job_results(client, job, job['input_file'])
                            # Download result is for internal processing only
                        
                        # Clean up resources regardless of success/failure
                        cleanup_job_resources(client, job)
                        
                        # Record completion time and final state
                        update_job_completion(job_info_file, jobs, i, completed_at, current_state)
                        newly_completed += 1
                    
                except Exception as e:
                    # Errors are for internal processing only, don't affect display
                    pass
            
            if newly_completed > 0:
                # Reload job information and continue to next loop
                continue
            
            # Wait if there are still incomplete jobs
            remaining = len(get_pending_jobs(load_jobs_from_file(job_info_file)))
            if remaining > 0:
                for countdown in range(POLL_INTERVAL, -1, -1):
                    live.update(create_job_status_display(jobs, current_time, countdown))
                    time.sleep(1)


def main_with_args(args, client):
    """Main function that accepts parsed arguments and initialized client"""
    
    # Poll jobs
    try:
        poll_jobs(args.job_info, client)
        print("\nPolling completed")
    except KeyboardInterrupt:
        print("\nPolling interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: Unexpected error during polling: {e}", file=sys.stderr)
        sys.exit(1)
