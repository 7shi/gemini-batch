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
            job_name = job_info["job_name"]
            input_file = job_info["input_file"]
            
            batch_dict = get_batch_info(client, job_name)
            
            result = {
                "input_file": input_file,
                "batch": batch_dict
            }
            
            print(json.dumps(result))

if __name__ == "__main__":
    main()
