#!/usr/bin/env python3
"""Dataset cleaning script for Task 1.

Reads shard outputs from datasets/teacher/ (or input arguments),
validates each teacher reply against schema rules (a)-(e),
sorts by id, and outputs:
  datasets/v1/train.jsonl
  datasets/v1/train.sha256
Prints exact count breakdown:
  input = (a) + (b) + (c) + (d) + (e/duplicates) + kept
"""
import glob
import hashlib
import json
import os
import sys

VALID_INTENTS = {
    "alarm_set",
    "alarm_query",
    "calendar_set",
    "calendar_query",
    "calendar_remove",
    "weather_query",
    "datetime_query",
    "recommendation_events",
}

REQUIRED_KEYS = {"intent", "date", "time", "place"}


def parse_raw(raw):
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return None
    raw_str = raw.strip()
    # Strip markdown code blocks if present
    if raw_str.startswith("```json"):
        raw_str = raw_str[7:]
    if raw_str.startswith("```"):
        raw_str = raw_str[3:]
    if raw_str.endswith("```"):
        raw_str = raw_str[:-3]
    raw_str = raw_str.strip()
    try:
        obj = json.loads(raw_str)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return None


def clean_shards(shard_paths, output_jsonl, output_sha):
    raw_records = []
    seen_ids = set()

    for p in shard_paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec["id"] in seen_ids:
                    continue
                seen_ids.add(rec["id"])
                raw_records.append(rec)

    # Sort all input records by ID first to ensure deterministic evaluation and smallest id priority
    raw_records.sort(key=lambda r: r["id"])

    total_input = len(raw_records)
    count_a = 0  # not valid JSON
    count_b = 0  # keys not exactly 4
    count_c = 0  # intent not in 8
    count_d = 0  # slot not in text and not null
    count_duplicates = 0  # duplicate commands
    kept_records = []
    seen_texts = set()

    for rec in raw_records:
        cmd_text = rec.get("text", "")
        raw_reply = rec.get("teacher_raw")

        # Check (a): valid JSON
        parsed = parse_raw(raw_reply)
        if parsed is None:
            count_a += 1
            continue

        # Check (b): keys exactly intent, date, time, place
        if set(parsed.keys()) != REQUIRED_KEYS:
            count_b += 1
            continue

        # Check (c): intent is one of the eight
        if parsed.get("intent") not in VALID_INTENTS:
            count_c += 1
            continue

        # Check (d): slot value is either null or text in command
        bad_slot = False
        text_lower = cmd_text.lower()
        for k in ("date", "time", "place"):
            val = parsed.get(k)
            if val is not None:
                if not isinstance(val, str) or val.strip().lower() not in text_lower:
                    bad_slot = True
                    break
        if bad_slot:
            count_d += 1
            continue

        # Check (e): duplicate commands (keep smallest id, which is seen first due to sorting)
        normalized_text = " ".join(cmd_text.strip().lower().split())
        if normalized_text in seen_texts:
            count_duplicates += 1
            continue
        seen_texts.add(normalized_text)

        # Kept record
        kept_records.append({
            "id": rec["id"],
            "text": cmd_text,
            "reply": parsed
        })

    # Write output
    os.makedirs(os.path.dirname(output_jsonl), exist_ok=True)
    with open(output_jsonl, "w", encoding="utf-8") as f:
        for r in kept_records:
            f.write(json.dumps(r) + "\n")

    # Compute SHA-256
    with open(output_jsonl, "rb") as f:
        file_sha = hashlib.sha256(f.read()).hexdigest()

    with open(output_sha, "w", encoding="utf-8") as f:
        f.write(file_sha + "\n")

    print("\n=== Dataset Cleaning Summary ===")
    print(f"Total Input Records   : {total_input}")
    print(f"(a) Invalid JSON      : {count_a}")
    print(f"(b) Incorrect Keys    : {count_b}")
    print(f"(c) Invalid Intent    : {count_c}")
    print(f"(d) Hallucinated Slot : {count_d}")
    print(f"(e) Duplicate Commands: {count_duplicates}")
    print(f"Kept Records          : {len(kept_records)}")
    print(f"Sum of parts          : {count_a + count_b + count_c + count_d + count_duplicates + len(kept_records)}")
    print(f"Match Check           : {total_input == count_a + count_b + count_c + count_d + count_duplicates + len(kept_records)}")
    print(f"SHA-256 Checksum      : {file_sha}")
    print(f"Output File           : {output_jsonl}")

    # Save summary stats as json for inclusion in report
    summary = {
        "total_input": total_input,
        "invalid_json_a": count_a,
        "incorrect_keys_b": count_b,
        "invalid_intent_c": count_c,
        "invalid_slot_d": count_d,
        "duplicates_e": count_duplicates,
        "kept": len(kept_records),
        "sha256": file_sha
    }
    with open(os.path.join(os.path.dirname(output_jsonl), "cleaning_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    shards = sorted(glob.glob("datasets/teacher/shard-*.jsonl"))
    if not shards:
        # Check alternative location
        shards = sorted(glob.glob("data/teacher/shard-*.jsonl"))
    if not shards:
        print("No shard files found in datasets/teacher/ or data/teacher/")
        sys.exit(1)

    out_file = "datasets/v1/train.jsonl"
    sha_file = "datasets/v1/train.sha256"
    clean_shards(shards, out_file, sha_file)

