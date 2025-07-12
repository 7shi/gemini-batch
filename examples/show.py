#!/usr/bin/env python3

import json
from pathlib import Path

examples_dir = Path(__file__).parent

for i, jsonl_file in enumerate(sorted(examples_dir.glob("*.jsonl"))):
    if i:
        print()
    print("##", jsonl_file.name)
    with open(jsonl_file) as f:
        for j, line in enumerate(f, 1):
            if line.strip():
                data = json.loads(line)
                request = data["request"]
                text = request["contents"][0]["parts"][0]["text"]
                print()
                print("###", j)
                print(text)
                
                if "generation_config" in request and "response_schema" in request["generation_config"]:
                    schema = request["generation_config"]["response_schema"]
                    print("```json")
                    print(json.dumps(schema, indent=2))
                    print("```")
