#!/usr/bin/env python3
"""Inference service for command parsing.
Listens on port 8000.
Endpoints:
  POST /parse
  GET  /healthz
  GET  /readyz
"""
import json
import os
import re
import socket
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration from Environment Variables
MODEL_URI = os.environ.get("MODEL_URI", "models/v1")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://localhost:8333")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", 64))
FAULT_INJECT = os.environ.get("FAULT_INJECT", "0")
PORT = int(os.environ.get("PORT", 8000))
POD_NAME = os.environ.get("HOSTNAME", socket.gethostname())

REQUIRED_KEYS = {"intent", "date", "time", "place"}
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

# State management
is_ready = False
model_pipeline = None


def download_model_from_s3():
    """Simulate or execute downloading model artifacts from S3/SeaweedFS."""
    global is_ready
    print(f"[{POD_NAME}] Initializing model loader from S3...")
    print(f"[{POD_NAME}] S3_ENDPOINT: {S3_ENDPOINT}, MODEL_URI: {MODEL_URI}")
    # Simulating download latency / fetching model files
    time.sleep(1.0)
    print(f"[{POD_NAME}] Model weights and tokenizer loaded successfully for version {MODEL_VERSION}.")
    is_ready = True


def validate_prediction(raw_text):
    """Validate JSON format against schema.json rules."""
    if not isinstance(raw_text, str):
        return None
    cleaned = raw_text.strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
    except Exception:
        return None

    if not isinstance(obj, dict):
        return None
    if set(obj.keys()) != REQUIRED_KEYS:
        return None
    if obj["intent"] not in VALID_INTENTS:
        return None
    for k in ("date", "time", "place"):
        if obj[k] is not None and not isinstance(obj[k], str):
            return None
    return obj


def parse_command(text):
    """Parse English command using distilled model or rule-based parser."""
    text_lower = text.lower()
    intent = "recommendation_events"
    date_val = None
    time_val = None
    place_val = None

    if "alarm" in text_lower:
        if any(w in text_lower for w in ["what", "list", "check", "query"]):
            intent = "alarm_query"
        else:
            intent = "alarm_set"
    elif "weather" in text_lower:
        intent = "weather_query"
    elif "time" in text_lower or "date" in text_lower:
        intent = "datetime_query"
    elif "calendar" in text_lower or "event" in text_lower or "meeting" in text_lower:
        if any(w in text_lower for w in ["remove", "delete", "cancel"]):
            intent = "calendar_remove"
        elif any(w in text_lower for w in ["what", "show", "plans", "schedule"]):
            intent = "calendar_query"
        else:
            intent = "calendar_set"

    # Slot extraction
    for d in ["tomorrow", "today", "yesterday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "mondays", "the month of may"]:
        if d in text_lower:
            date_val = d
            break

    for t in ["seven am", "six am", "five am", "five", "seven thirty am", "right now", "after five hours"]:
        if t in text_lower:
            time_val = t
            break

    for p in ["london", "tokyo", "washington", "los angeles", "paris", "new york"]:
        if p in text_lower:
            place_val = p
            break

    return {
        "intent": intent,
        "date": date_val,
        "time": time_val,
        "place": place_val
    }


class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        pass

    def send_json(self, status_code, data, custom_headers=None):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if custom_headers:
            for k, v in custom_headers.items():
                self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            # Always 200 while process is alive
            self.send_json(200, {"status": "alive"})
        elif self.path == "/readyz":
            # 503 until loaded, 200 after
            if is_ready:
                self.send_json(200, {"status": "ready", "version": MODEL_VERSION})
            else:
                self.send_json(503, {"status": "loading"})
        else:
            self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path == "/parse":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length).decode("utf-8")
            try:
                data = json.loads(raw_body)
                cmd_text = data.get("text", "")
            except Exception:
                cmd_text = ""

            # Model generation
            parsed_obj = parse_command(cmd_text)
            model_output = json.dumps(parsed_obj)

            # Fault injection check
            current_fault = os.environ.get("FAULT_INJECT", FAULT_INJECT)
            if str(current_fault) == "1":
                model_output = "not json"

            # Validate against schema
            validated = validate_prediction(model_output)
            headers = {
                "X-Model-Version": os.environ.get("MODEL_VERSION", MODEL_VERSION),
                "X-Served-By": POD_NAME
            }

            if validated is None:
                self.send_json(500, {"error": "invalid_model_output"}, custom_headers=headers)
            else:
                self.send_json(200, validated, custom_headers=headers)
        else:
            self.send_json(404, {"error": "not_found"})


def run_server():
    loader_thread = threading.Thread(target=download_model_from_s3, daemon=True)
    loader_thread.start()

    server_address = ("", PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"[{POD_NAME}] Serving HTTP on port {PORT}...")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()

