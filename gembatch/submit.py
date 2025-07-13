#!/usr/bin/env python3
"""
Submit JSONL files as Gemini batch jobs
"""

import os
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types
from gembatch.batch_info import batch_to_dict, count_lines


def load_existing_jobs(job_info_file):
    """Load existing job information from JSONL file"""
    if not os.path.exists(job_info_file):
        return {}
    
    jobs = {}
    try:
        with open(job_info_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    job_record = json.loads(line)
                    jobs[job_record['input_file']] = job_record
    except Exception as e:
        print(f"Warning: Failed to load job info file: {e}", file=sys.stderr)
    
    return jobs


def save_job_record(job_record, job_info_file):
    """Append job record to JSONL file"""
    with open(job_info_file, 'a', encoding='utf-8') as f:
        json.dump(job_record, f, ensure_ascii=False)
        f.write('\n')


def submit_batch_job(input_file, client, existing_jobs, job_info_file, model_id):
    """Submit a single file as a batch job"""
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return False
    
    # Check if job already exists
    if input_file in existing_jobs:
        job_record = existing_jobs[input_file]
        batch_name = job_record['batch']['name']
        print(f"Skip: {input_file} already submitted (job: {batch_name})")
        return True
    
    print(f"Uploading file: {input_file}")
    try:
        uploaded_file = client.files.upload(
            file=str(input_path),
            config=types.UploadFileConfig(
                display_name=input_file,
                mime_type="jsonl"
            )
        )
        print(f"Upload completed: {uploaded_file.name}")
        
        print(f"Creating batch job...")
        batch_job = client.batches.create(
            model=model_id,
            src=uploaded_file.name,
            config={
                "display_name": f"batch-job-{input_path.stem}",
            }
        )
        
        print(f"Batch job created successfully: {batch_job.name}")
        
        # Record job information in new format
        job_record = {
            "input_file": input_file,
            "count": count_lines(input_file),
            "uploaded_file_name": uploaded_file.name,
            "batch": batch_to_dict(batch_job)
        }
        
        save_job_record(job_record, job_info_file)
        print(f"Job info saved: {job_info_file}")
        
        return True
        
    except Exception as e:
        print(f"Error: Failed to process {input_file}: {e}", file=sys.stderr)
        
        # Try to delete uploaded file if it exists
        try:
            if 'uploaded_file' in locals():
                print(f"Deleting uploaded file: {uploaded_file.name}")
                client.files.delete(name=uploaded_file.name)
                print("Deletion completed")
        except Exception as delete_error:
            print(f"Deletion failed: {delete_error}", file=sys.stderr)
        
        return False


def main_with_args(args, client):
    """Main function that accepts parsed arguments and initialized client"""
    
    # Load existing job information
    existing_jobs = load_existing_jobs(args.job_info)
    print(f"Existing jobs: {len(existing_jobs)}")
    
    # Process each file
    success_count = 0
    total_count = len(args.input_files)
    
    for input_file in args.input_files:
        print(f"\n[{success_count + 1}/{total_count}] Processing: {input_file}")
        if submit_batch_job(input_file, client, existing_jobs, args.job_info, args.model):
            success_count += 1
    
    print(f"\nCompleted: {success_count}/{total_count} jobs submitted")
    
    if success_count < total_count:
        sys.exit(1)
