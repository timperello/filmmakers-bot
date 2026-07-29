import requests
import os

WEBHOOK = os.environ["WEBHOOK"]

r = requests.post(WEBHOOK, json={"content": "test"}, timeout=10)
print("Status code:", r.status_code)
print("Response:", r.text)
