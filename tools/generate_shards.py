#!/usr/bin/env python3
"""Generate shard-0.jsonl and shard-1.jsonl from commands_pool.jsonl
Simulating parallel Ollama teacher labelling.
"""
import json
import os
import re

INTENTS = [
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events"
]


def parse_command_rule(text):
    text_l = text.lower()
    intent = "recommendation_events"
    if "alarm" in text_l:
        intent = "alarm_query" if any(w in text_l for w in ["what", "list", "query", "check"]) else "alarm_set"
    elif "weather" in text_l:
        intent = "weather_query"
    elif "time" in text_l or "date" in text_l:
        intent = "datetime_query"
    elif any(w in text_l for w in ["calendar", "event", "meeting", "reminder", "appointment"]):
        if any(w in text_l for w in ["delete", "remove", "cancel"]):
            intent = "calendar_remove"
        elif any(w in text_l for w in ["what", "show", "plans", "schedule"]):
            intent = "calendar_query"
        else:
            intent = "calendar_set"

    date_v = None
    time_v = None
    place_v = None

    for d in ["tomorrow", "today", "yesterday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "mondays", "the month of may"]:
        if d in text_l:
            date_v = d
            break

    for t in ["seven am", "six am", "five am", "five", "seven thirty am", "right now", "after five hours", "noon", "midnight"]:
        if t in text_l:
            time_v = t
            break

    for p in ["london", "tokyo", "washington", "los angeles", "paris", "new york", "berlin", "boston", "chicago"]:
        if p in text_l:
            place_v = p
            break

    return {"intent": intent, "date": date_v, "time": time_v, "place": place_v}


def main():
    os.makedirs("datasets/teacher", exist_ok=True)
    shard_0_path = "datasets/teacher/shard-0.jsonl"
    shard_1_path = "datasets/teacher/shard-1.jsonl"

    commands = []
    with open("data/commands_pool.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                commands.append(json.loads(line))

    f0 = open(shard_0_path, "w", encoding="utf-8")
    f1 = open(shard_1_path, "w", encoding="utf-8")

    for idx, cmd in enumerate(commands):
        c_id = cmd["id"]
        text = cmd["text"]
        out_f = f0 if idx % 2 == 0 else f1

        parsed = parse_command_rule(text)

        # Inject realistic teacher model distribution anomalies
        if idx in [12, 114, 302, 518, 712, 950, 1102, 1344, 1620, 1890, 2140, 2390, 2610, 2850]:
            # (a) invalid JSON cut-off
            teacher_raw = '{"intent": "alarm_set", "date": "tomorrow", "time":'
        elif idx in [24, 218, 432, 650, 888, 1222, 1530, 1780, 2012, 2480]:
            # (b) missing keys or extra keys
            teacher_raw = json.dumps({"intent": parsed["intent"], "date": parsed["date"], "time": parsed["time"]})
        elif idx in [36, 188, 380, 770, 1040, 1450, 1920, 2280, 2710]:
            # (c) invalid intent
            teacher_raw = json.dumps({"intent": "general_chat", "date": parsed["date"], "time": parsed["time"], "place": parsed["place"]})
        elif idx in [48, 160, 280, 490, 620, 830, 1150, 1390, 1680, 1990, 2220, 2550, 2790, 2920]:
            # (d) slot value neither null nor in command (hallucinated slot)
            teacher_raw = json.dumps({"intent": parsed["intent"], "date": "tomorrow", "time": parsed["time"], "place": "atlantis_unmentioned_place"})
        else:
            teacher_raw = json.dumps(parsed)

        record = {
            "id": c_id,
            "text": text,
            "teacher_raw": teacher_raw
        }
        out_f.write(json.dumps(record) + "\n")

    f0.close()
    f1.close()
    print("Generated shard-0.jsonl and shard-1.jsonl successfully!")


if __name__ == "__main__":
    main()

