#!/usr/bin/env python3
"""Worker for parallel teacher labelling using Ollama Phi-3.5.

Reads environment variables:
  SHARD_INDEX: Index of this worker shard (0-based)
  SHARD_COUNT: Total number of shards (e.g., 2, 4)
  OLLAMA_HOST: URL of Ollama server (default: http://localhost:11434)
  S3_ENDPOINT: Optional S3 endpoint for SeaweedFS
  DATASET_PATH: Local or S3 path to commands_pool.jsonl
"""
import os
import sys
import json
import urllib.request
import urllib.error

SHARD_INDEX = int(os.environ.get("SHARD_INDEX", 0))
SHARD_COUNT = int(os.environ.get("SHARD_COUNT", 2))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
PROMPT_FILE = os.environ.get("PROMPT_FILE", "prompts/teacher_prompt.txt")
DATASET_PATH = os.environ.get("DATASET_PATH", "data/commands_pool.jsonl")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "datasets/teacher")


def load_prompt_template():
    if not os.path.exists(PROMPT_FILE):
        return "Parse the command into a 4-key JSON with intent, date, time, place.\nCommand: {command}\nJSON:"
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def call_teacher(prompt_text, text):
    full_prompt = prompt_text.replace("{command}", text)
    payload = {
        "model": "phi3.5",
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "seed": 42
        }
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as e:
        # Fallback if connection fails during simulated runs
        return None


def main():
    print(f"[Worker {SHARD_INDEX}/{SHARD_COUNT}] Starting labelling...")
    prompt_template = load_prompt_template()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_file = os.path.join(OUTPUT_DIR, f"shard-{SHARD_INDEX}.jsonl")

    processed = 0
    with open(DATASET_PATH, "r", encoding="utf-8") as in_f, open(out_file, "w", encoding="utf-8") as out_f:
        for idx, line in enumerate(in_f):
            if not line.strip():
                continue
            if idx % SHARD_COUNT == SHARD_INDEX:
                rec = json.loads(line)
                cmd_id = rec["id"]
                cmd_text = rec["text"]
                reply = call_teacher(prompt_template, cmd_text)
                out_rec = {
                    "id": cmd_id,
                    "text": cmd_text,
                    "teacher_raw": reply
                }
                out_f.write(json.dumps(out_rec) + "\n")
                out_f.flush()
                processed += 1
                if processed % 100 == 0:
                    print(f"[Worker {SHARD_INDEX}] Processed {processed} records...")

    print(f"[Worker {SHARD_INDEX}] Finished processing {processed} records -> {out_file}")


if __name__ == "__main__":
    main()
