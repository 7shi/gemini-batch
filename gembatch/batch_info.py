#!/usr/bin/env python3
import argparse
import json
import os
from google import genai

def batch_to_dict(batch_job):
    """Convert BatchJob object to dictionary"""
    batch_dict = {
        "name": batch_job.name,
        "display_name": batch_job.display_name,
        "model": batch_job.model,
        "state": batch_job.state.name,
        "create_time": batch_job.create_time.isoformat() if batch_job.create_time else "",
        "update_time": batch_job.update_time.isoformat() if batch_job.update_time else "",
        "end_time": batch_job.end_time.isoformat() if batch_job.end_time else "",
    }
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
    # Check if already in new format and count exists
    if "batch" in job_info and job_info.get("count"):
        return None  # No conversion needed
    
    input_file = job_info["input_file"]
    
    # If batch field exists but count is missing/zero, add count
    if "batch" in job_info:
        return {
            "input_file": input_file,
            "count": count_lines(input_file),
            "batch": job_info["batch"]
        }
    
    # Legacy format: fetch batch info from API
    job_name = job_info["job_name"]
    batch_dict = get_batch_info(client, job_name)
    count = count_lines(input_file)
    
    return {
        "input_file": input_file,
        "count": count,
        "batch": batch_dict
    }

def main():
    parser = argparse.ArgumentParser(description="Process batch job information from JSONL file")
    parser.add_argument("input_file", help="Input JSONL file containing job information")
    args = parser.parse_args()
    
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"api_version": "v1alpha"})
    
    with open(args.input_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            job_info = json.loads(line)
            
            result = convert_job_if_needed(client, job_info)
            if result is None:
                result = job_info  # Use original if no conversion needed
            
            print(json.dumps(result))

if __name__ == "__main__":
    main()
