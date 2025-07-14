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
from datetime import datetime, timezone
from pathlib import Path
from google import genai
from rich.live import Live
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from gembatch.batch_info import batch_to_dict, convert_job_if_needed

POLL_INTERVAL = 30  # Poll every 30 seconds

console = Console()


def to_local_time(iso_time_str):
    """Convert ISO time string to local time string"""
    if not iso_time_str:
        return ""
    try:
        # Parse ISO format and convert to local time
        dt = datetime.fromisoformat(iso_time_str.replace('Z', '+00:00'))
        local_dt = dt.astimezone()
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return iso_time_str[:19].replace('T', ' ')


class JobStatusDisplay:
    """Updatable job status display"""
    def __init__(self, jobs, last_update, checking_job_index=None):
        self.jobs = jobs
        self.last_update = last_update
        self.checking_job_index = checking_job_index
        self.summary_text = Text()
        self.last_update_text = Text(f"Last update: {last_update}", style="dim")
        self.countdown_text = Text()
        self._build_display()
    
    def _build_display(self):
        # Build table
        self.table = Table(title="Batch Job Monitor")
        self.table.add_column("Input File", style="cyan")
        self.table.add_column("Count", style="blue", justify="right")
        self.table.add_column("State", style="magenta")
        self.table.add_column("Create Time", style="dim")
        self.table.add_column("End Time", style="green")
        self.table.add_column("Duration", style="yellow", justify="right")
        
        completed_count = 0
        for job_index, job in enumerate(self.jobs):
            input_file = job['input_file']
            count = job.get('count', 0)
            batch = job['batch']
            batch_state = batch.get('state', '')
            
            if batch_state in ['JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED']:
                completed_count += 1
                if batch_state == 'JOB_STATE_SUCCEEDED':
                    status = "✓ Success"
                    status_style = "green"
                elif batch_state == 'JOB_STATE_FAILED':
                    status = "✗ Failed"
                    status_style = "red"
                elif batch_state == 'JOB_STATE_CANCELLED':
                    status = "⊘ Cancelled"
                    status_style = "orange1"
                else:
                    status = "✓ Completed"
                    status_style = "green"
            else:
                status = "⏳ Running"
                # Check if this specific job is being checked
                if self.checking_job_index == job_index:
                    status_style = "white on red"
                else:
                    status_style = "yellow"
            
            # Extract times from batch object and convert to local time
            create_time = batch.get('create_time', '')
            end_time = batch.get('end_time', '')
            created_at = to_local_time(create_time)
            completed_at = to_local_time(end_time)
            
            # Calculate duration from create_time and end_time (or current time)
            duration_display = ""
            if create_time:
                try:
                    create_dt = datetime.fromisoformat(create_time.replace('Z', '+00:00'))
                    if end_time:
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    else:
                        end_dt = datetime.now(timezone.utc)
                    duration = end_dt - create_dt
                    duration_sec = int(duration.total_seconds())
                    
                    hours = duration_sec // 3600
                    minutes = (duration_sec % 3600) // 60
                    seconds = duration_sec % 60
                    duration_display = f"{hours}:{minutes:02d}:{seconds:02d}"
                except Exception:
                    duration_display = ""
            
            # Format count with comma separator
            count_display = f"{count:,}" if count > 0 else ""
            
            self.table.add_row(
                input_file,
                count_display,
                Text(status, style=status_style),
                created_at,
                completed_at,
                duration_display
            )
        
        # Build summary
        total_jobs = len(self.jobs)
        self.pending_jobs = total_jobs - completed_count
        self._update_summary()
    
    def _update_summary(self, countdown=None, checking=False):
        total_jobs = len(self.jobs)
        completed_count = total_jobs - self.pending_jobs
        
        # Build combined summary and countdown text
        self.summary_text.plain = ""
        self.summary_text.append(f"Total jobs: {total_jobs} | ", style="bold")
        self.summary_text.append(f"Completed: {completed_count} | ", style="green bold")
        self.summary_text.append(f"Remaining: {self.pending_jobs}", style="yellow bold")
        
        # Add status or countdown
        if checking:
            self.summary_text.append(" | Checking status...", style="orange1 bold")
        elif countdown is not None:
            self.summary_text.append(f" | Next poll: {countdown}s", style="cyan")
    
    def update_countdown(self, countdown):
        """Update only the countdown part"""
        self._update_summary(countdown)
    
    def set_checking_status(self):
        """Set checking status message and rebuild display"""
        self._build_display()
        if self.checking_job_index is not None:
            self._update_summary(checking=True)
        else:
            self._update_summary()
    
    def __rich__(self):
        panel_content = [
            self.last_update_text,
            Text(""),
            self.table,
            Text(""),
            Align.left(self.summary_text)
        ]
        
        if self.pending_jobs == 0:
            panel_content.append(Text(""))
            panel_content.append(Text("🎉 All jobs completed!", style="green bold"))
        
        return Panel(
            Align.center(Columns(panel_content, equal=True, expand=True)),
            title="Gemini Batch Job Monitor",
            border_style="blue"
        )


def create_job_status_display(jobs, last_update, countdown=None):
    """Create a table display for job status (legacy function)"""
    display = JobStatusDisplay(jobs, last_update)
    if countdown is not None:
        display.update_countdown(countdown)
    return display


def load_jobs_from_file(job_info_file, client=None):
    """Load job information from JSONL file and convert if needed"""
    if not os.path.exists(job_info_file):
        print(f"Error: Job info file not found: {job_info_file}", file=sys.stderr)
        return [], False
    
    jobs = []
    conversion_needed = False
    
    try:
        with open(job_info_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        job_record = json.loads(line)
                        
                        # Check if conversion is needed
                        if client:
                            converted = convert_job_if_needed(client, job_record)
                            if converted is not None:
                                job_record = converted
                                conversion_needed = True
                        
                        jobs.append(job_record)
                    except json.JSONDecodeError as e:
                        print(f"Warning: JSON parse error at line {line_num}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error: Failed to load job info file: {e}", file=sys.stderr)
        return [], False
    
    return jobs, conversion_needed


def get_pending_jobs(jobs):
    """Get list of incomplete jobs"""
    pending = []
    for job in jobs:
        batch_state = job['batch'].get('state', '')
        if batch_state not in ['JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED']:
            pending.append(job)
    return pending


def write_updated_jobs(job_info_file, jobs):
    """Write updated jobs to JSONL file"""
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, 
                                       dir=os.path.dirname(job_info_file),
                                       prefix=f"{os.path.basename(job_info_file)}.tmp") as f:
            temp_file = f.name
            for job in jobs:
                json.dump(job, f, ensure_ascii=False)
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
    # Delete source file if it exists
    uploaded_file_name = job.get('uploaded_file_name')
    if uploaded_file_name:
        try:
            client.files.delete(name=uploaded_file_name)
        except Exception:
            # Ignore errors (might already be deleted)
            pass
    
    # Delete batch job
    job_name = job['batch']['name']
    try:
        client.batches.delete(name=job_name)
    except Exception:
        # Ignore errors (might already be deleted)
        pass


def download_job_results(client, job, input_file_path):
    """Download job results"""
    try:
        job_name = job['batch']['name']
        
        # Get latest job status
        batch_job = client.batches.get(name=job_name)
        
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
    with Live(console=console, auto_refresh=False) as live:
        while True:
            # Load latest job information
            jobs, conversion_needed = load_jobs_from_file(job_info_file, client)
            if not jobs:
                live.update(Text("Error: No jobs found", style="red bold"))
                live.refresh()
                break
            
            # Write updated jobs if conversion was needed
            if conversion_needed:
                write_updated_jobs(job_info_file, jobs)
            
            # Get incomplete jobs
            pending_jobs = get_pending_jobs(jobs)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update display
            live.update(create_job_status_display(jobs, current_time))
            live.refresh()
            
            # Exit loop if all jobs are completed
            if not pending_jobs:
                break
            
            # Check status of each incomplete job
            newly_completed = 0
            
            for i, job in enumerate(jobs):
                job_name = job['batch']['name']
                batch_state = job['batch'].get('state', '')
                
                # Skip if already completed
                if batch_state in ['JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED']:
                    continue
                
                # Show checking status for this specific job
                display = JobStatusDisplay(jobs, current_time, checking_job_index=i)
                live.update(display)
                live.refresh()
                
                try:
                    batch_job = client.batches.get(name=job_name)
                    current_state = batch_job.state.name
                    
                    # Update job with new batch information immediately
                    job['batch'] = batch_to_dict(batch_job)
                    
                    if current_state != "JOB_STATE_PENDING":
                        # Job completed (success, failure, or cancellation)
                        if current_state == "JOB_STATE_SUCCEEDED":
                            # Download results
                            success, message = download_job_results(client, job, job['input_file'])
                            # Download result is for internal processing only
                        
                        # Clean up resources regardless of success/failure
                        cleanup_job_resources(client, job)
                        
                        # Write updated job info
                        write_updated_jobs(job_info_file, jobs)
                        newly_completed += 1
                    
                except Exception as e:
                    # Errors are for internal processing only, don't affect display
                    pass
            
            if newly_completed > 0:
                # Reload job information and continue to next loop
                continue
            
            # Wait if there are still incomplete jobs
            remaining = len(get_pending_jobs(jobs))
            if remaining > 0:
                # Create display object once
                display = JobStatusDisplay(jobs, current_time)
                for countdown in range(POLL_INTERVAL, -1, -5):
                    display.update_countdown(countdown)
                    live.update(display)
                    live.refresh()
                    if countdown > 0:
                        time.sleep(5)


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
