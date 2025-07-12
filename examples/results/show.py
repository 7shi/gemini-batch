#!/usr/bin/env python3

import json
import re
from pathlib import Path

results_dir = Path(__file__).parent
examples_dir = results_dir.parent

for i, jsonl_file in enumerate(sorted(results_dir.glob("*.jsonl"))):
    if i:
        print()
    print("##", jsonl_file.name)
    
    # Read corresponding prompt file
    prompt_file = examples_dir / jsonl_file.name
    prompts = []
    if prompt_file.exists():
        with open(prompt_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    text = data["request"]["contents"][0]["parts"][0]["text"]
                    prompts.append(text)
    
    with open(jsonl_file) as f:
        for j, line in enumerate(f, 1):
            if line.strip():
                data = json.loads(line)
                response = data["response"]
                text = response["candidates"][0]["content"]["parts"][0]["text"]
                print()
                print("###", j)
                
                # Show prompt if available
                if j <= len(prompts):
                    print(">", prompts[j-1])
                    print()
                
                if text.startswith("{"):
                    print("```json")
                    print(text)
                    print("```")
                else:
                    text = re.sub(r"^(#+)\s+(.*)$", r"**\2**", text, flags=re.MULTILINE)
                    print(text)
