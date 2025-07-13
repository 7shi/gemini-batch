#!/usr/bin/env python3
"""
Clean up Gemini batch resources (files and batch jobs)
"""

import sys
import os
import argparse
from google import genai


def main_with_args(args, client):
    """Main function that accepts parsed arguments and initialized client"""
    
    print("=== File List ===")
    files = list(client.files.list())
    for file in files:
        print(f"- {file.name}")

    print("\n=== Batch Job List ===")
    batches = list(client.batches.list())
    for batch in batches:
        print(f"- {batch.name}")

    print()
    if not files and not batches:
        print("No resources to delete.")
        return

    print(f"Targets to delete: {len(files)} files, {len(batches)} batch jobs")
    
    if not args.yes:
        confirm = input("Delete all? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            print("Deletion cancelled.")
            return

    for file in files:
        print(f"Deleting file: {file.name}")
        try:
            client.files.delete(name=file.name)
            print("Deleted.")
        except Exception as e:
            print(f"Error occurred during deletion: {e}", file=sys.stderr)

    for batch in batches:
        print(f"Deleting batch job: {batch.name}")
        try:
            client.batches.delete(name=batch.name)
            print("Deleted.")
        except Exception as e:
            print(f"Error occurred during deletion: {e}", file=sys.stderr)

    print("\nCleanup completed.")
