#!/usr/bin/env python3
"""
Submit JSONL files as Gemini batch jobs
"""
import sys
import argparse
from pathlib import Path
from google import genai
from google.genai import types
from gembatch.batch_info import batch_to_dict, count_lines, AtomicJobManager


def submit_batch_job(input_file, client, manager, model_id):
    """Submit a single file as a batch job"""
    # Check if file exists
    if not manager.file_exists(input_file):
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return False
    
    # Check if job already exists
    existing_job = manager.find_job_by_input_file(input_file)
    if existing_job:
        batch_name = existing_job['batch']['name']
        print(f"Skip: {input_file} already submitted (job: {batch_name})")
        return True
    
    print(f"Uploading file: {input_file}")
    try:
        uploaded_file = client.files.upload(
            file=str(Path(input_file)),
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
                "display_name": input_file,
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
        
        # Add job to manager (atomically saved on context exit)
        success = manager.add_job(job_record)
        if success:
            print(f"Job info will be saved")
        
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
    
    # Process all files under a single lock to prevent race conditions
    with AtomicJobManager(args.job_info, client) as manager:
        existing_count = len(manager.get_all_jobs())
        print(f"Existing jobs: {existing_count}")
        
        # Process each file
        success_count = 0
        total_count = len(args.input_files)
        
        for input_file in args.input_files:
            print(f"\n[{success_count + 1}/{total_count}] Processing: {input_file}")
            if submit_batch_job(input_file, client, manager, args.model):
                success_count += 1
        
        print(f"\nCompleted: {success_count}/{total_count} jobs submitted")
        # All changes will be saved atomically when exiting this context
        
    if success_count < total_count:
        sys.exit(1)
