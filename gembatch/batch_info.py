#!/usr/bin/env python3
import argparse
import json
import os
import time
from pathlib import Path
from google import genai

def batch_to_dict(batch_job):
    """Convert BatchJob object to dictionary"""
    batch_dict = {
        "name": batch_job.name,
        "display_name": batch_job.display_name,
        "model": batch_job.model,
        "state": batch_job.state.name,
    }
    if batch_job.create_time is not None:
        batch_dict["create_time"] = batch_job.create_time.isoformat()
    if batch_job.update_time is not None:
        batch_dict["update_time"] = batch_job.update_time.isoformat()
    if batch_job.end_time is not None:
        batch_dict["end_time"] = batch_job.end_time.isoformat()
    if batch_job.dest is not None:
        batch_dict["dest"] = {"file_name": batch_job.dest.file_name}
    return batch_dict

def get_batch_info(client, batch_name):
    """Get batch job information and return as dict"""
    batch = client.batches.get(name=batch_name)
    return batch_to_dict(batch)

def count_lines(filename):
    """Count non-empty lines in a file"""
    count = 0
    with open(filename, "r") as f:
        for line in f:
            if line.strip():
                count += 1
    return count

def convert_job_if_needed(client, job_info):
    """Convert job info if needed, return dict or None if no conversion needed"""
    input_file = job_info["input_file"]
    
    # If batch field exists but count is missing/zero, add count
    if "batch" in job_info:
        # Check if already in new format and count exists
        if "count" in job_info:
            return None  # No conversion needed
        
        result = {
            "input_file": input_file,
            "count": count_lines(input_file),
            "uploaded_file_name": job_info.get("uploaded_file_name", ""),
            "batch": job_info["batch"]
        }
        return result
    
    # Legacy format: fetch batch info from API
    job_name = job_info["job_name"]
    batch_dict = get_batch_info(client, job_name)
    count = count_lines(input_file)
    
    result = {
        "input_file": input_file,
        "count": count,
        "uploaded_file_name": job_info["uploaded_file_name"],
        "batch": batch_dict
    }
    return result


class AtomicJobManager:
    """Atomic job manager with file locking for safe concurrent access"""
    
    def __init__(self, job_info_file, client=None, timeout=30, retry_interval=1, read_only=False):
        self.job_info_file = job_info_file
        self.client = client
        self.timeout = timeout
        self.retry_interval = retry_interval
        self.read_only = read_only
        self.tmp_file = f"{job_info_file}.tmp"
        self.tmp_file_obj = None
        self.jobs = []
        self.conversion_occurred = False
        self.modifications_made = False
        
    def __enter__(self):
        """Acquire lock and load jobs"""
        start_time = time.time()
        
        while True:
            try:
                # Try to create tmp file exclusively (atomic lock acquisition)
                self.tmp_file_obj = open(self.tmp_file, "x", encoding="utf-8")
                break
            except FileExistsError:
                # Lock file exists, wait and retry
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(f"Could not acquire lock on {self.job_info_file} within {self.timeout} seconds")
                time.sleep(self.retry_interval)
        
        # Load existing jobs
        self._load_jobs()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock and save if modifications were made"""
        try:
            if not self.read_only and (self.modifications_made or self.conversion_occurred):
                # Write all jobs to tmp file
                for job in self.jobs:
                    json.dump(job, self.tmp_file_obj, ensure_ascii=False)
                    self.tmp_file_obj.write('\n')
                self.tmp_file_obj.flush()
                self.tmp_file_obj.close()
                
                # Atomic replacement
                if os.path.exists(self.job_info_file):
                    os.remove(self.job_info_file)
                os.rename(self.tmp_file, self.job_info_file)
            else:
                # No changes or read-only mode, just remove tmp file
                self.tmp_file_obj.close()
                os.remove(self.tmp_file)
        except Exception:
            # Cleanup on error
            if self.tmp_file_obj and not self.tmp_file_obj.closed:
                self.tmp_file_obj.close()
            if os.path.exists(self.tmp_file):
                os.remove(self.tmp_file)
            raise
    
    def _load_jobs(self):
        """Load jobs from file and convert if needed"""
        self.jobs = []
        self.conversion_occurred = False
        
        if not os.path.exists(self.job_info_file):
            return
            
        try:
            with open(self.job_info_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            job_record = json.loads(line)
                            
                            # Check if conversion is needed
                            if self.client:
                                converted = convert_job_if_needed(self.client, job_record)
                                if converted is not None:
                                    job_record = converted
                                    self.conversion_occurred = True
                            
                            self.jobs.append(job_record)
                        except json.JSONDecodeError as e:
                            print(f"Warning: JSON parse error at line {line_num}: {e}")
        except Exception as e:
            print(f"Error: Failed to load job info file: {e}")
    
    def file_exists(self, filepath):
        """Check if file exists"""
        return Path(filepath).exists()
    
    def find_job_by_input_file(self, filename):
        """Find job by input file name"""
        for job in self.jobs:
            if job.get('input_file') == filename:
                return job
        return None
    
    def find_job_by_batch_name(self, batch_name):
        """Find job by batch name"""
        for job in self.jobs:
            if job.get('batch', {}).get('name') == batch_name:
                return job
        return None
    
    def add_job(self, job_record):
        """Add new job if not exists, return True if added, False if already exists"""
        if self.read_only:
            raise RuntimeError("Cannot add job in read-only mode")
        
        input_file = job_record.get('input_file')
        if self.find_job_by_input_file(input_file):
            return False
        
        self.jobs.append(job_record)
        self.modifications_made = True
        return True
    
    def update_job_by_batch_name(self, job_record):
        """Update job by batch name, return True if updated, False if not found"""
        if self.read_only:
            raise RuntimeError("Cannot update job in read-only mode")
        
        batch_name = job_record.get('batch', {}).get('name')
        if not batch_name:
            return False
        
        for i, job in enumerate(self.jobs):
            if job.get('batch', {}).get('name') == batch_name:
                self.jobs[i] = job_record
                self.modifications_made = True
                return True
        return False
    
    def get_all_jobs(self):
        """Get all jobs (for display purposes)"""
        return self.jobs.copy()
    
    def bulk_update_jobs(self, job_list):
        """Update multiple jobs efficiently"""
        updated_count = 0
        for job_record in job_list:
            if self.update_job_by_batch_name(job_record):
                updated_count += 1
        return updated_count > 0
    
    def was_converted(self):
        """Check if any job conversion occurred"""
        return self.conversion_occurred


def main():
    parser = argparse.ArgumentParser(description="Process batch job information from JSONL file")
    parser.add_argument("input_file", help="Input JSONL file containing job information")
    args = parser.parse_args()
    
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"api_version": "v1alpha"})
    
    # Use AtomicJobManager for safe file reading in read-only mode
    with AtomicJobManager(args.input_file, client, read_only=True) as manager:
        jobs = manager.get_all_jobs()
    
    # Output jobs (can be done outside the lock)
    for job in jobs:
        # Jobs are already converted by AtomicJobManager if needed
        print(json.dumps(job))

if __name__ == "__main__":
    main()
