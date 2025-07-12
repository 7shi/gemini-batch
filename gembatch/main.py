#!/usr/bin/env python3
"""
Main CLI entry point for Gemini Batch Tools
"""

import os
import sys
import argparse
from google import genai
from . import submit, poll

DEFAULT_MODEL = "gemini-2.5-flash-lite-preview-06-17"
DEFAULT_JOB_INFO_FILE = "job-info.jsonl"


def create_parser():
    """Create the main argument parser with subcommands"""
    parser = argparse.ArgumentParser(
        prog='gembatch',
        description='Command-line tools for managing Google Gemini batch jobs'
    )
    
    # Global arguments
    parser.add_argument(
        '--job-info',
        default=DEFAULT_JOB_INFO_FILE,
        help=f'JSONL file to store/read job information (default: {DEFAULT_JOB_INFO_FILE})'
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND'
    )
    
    # Submit subcommand
    submit_parser = subparsers.add_parser(
        'submit',
        help='Submit JSONL files as Gemini batch jobs'
    )
    submit_parser.add_argument(
        'input_files',
        nargs='+',
        help='JSONL file paths to submit (supports multiple files)'
    )
    submit_parser.add_argument(
        '-m', '--model',
        default=DEFAULT_MODEL,
        help=f'Gemini model to use (default: {DEFAULT_MODEL})'
    )
    
    # Poll subcommand
    poll_parser = subparsers.add_parser(
        'poll',
        help='Poll batch jobs and download results when completed'
    )
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Check Gemini API key
    if "GEMINI_API_KEY" not in os.environ:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    # Initialize Gemini client
    try:
        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"],
            http_options={"api_version": "v1alpha"}
        )
    except Exception as e:
        print(f"Error: Failed to initialize Gemini client: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.command == 'submit':
            return submit.main_with_args(args, client)
        elif args.command == 'poll':
            return poll.main_with_args(args, client)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
