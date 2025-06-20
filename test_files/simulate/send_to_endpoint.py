import os
import requests
import json
import time

endpoint = "http://localhost:5000/api/logs"

log_path = os.path.join(os.path.dirname(__file__), "shell_log.jsonl")

with open(log_path, "r", encoding="utf-8") as f:
    log_data = f.readlines()

log_data = [json.loads(log) for log in log_data]

for log in log_data:
    # print the first few characters of the log
    print(str(log)[:500] + ("..." if len(str(log)) > 500 else "") + "\n")

    time.sleep(0.5)
    requests.post(endpoint, json=log)