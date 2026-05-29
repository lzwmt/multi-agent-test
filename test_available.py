#!/usr/bin/env python3
import json
import os
import requests

API_URL = "http://127.0.0.1:8317/v1/chat/completions"
API_KEY = "cliproxy-lzwmt-2026"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-5-codex",
    "messages": [{"role": "user", "content": "hi"}]
}

auth_dir = "/home/cpa/CLIProxyAPI/auths"
available = []
failed = []

for f in os.listdir(auth_dir):
    if not f.endswith(".json"):
        continue
    path = os.path.join(auth_dir, f)
    try:
        with open(path, "r") as handle:
            acc = json.load(handle)
        print(f"Testing {acc['email']}...")
        r = requests.post(API_URL, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            print(f"✅ {acc['email']} - OK")
            available.append(acc["email"])
        else:
            err = r.json().get("error", {}).get("message", r.text)
            print(f"❌ {acc['email']} - {r.status_code}: {err[:100]}")
            failed.append((acc["email"], r.status_code, err))
    except Exception as e:
        print(f"❌ {f} - Exception: {e}")
        failed.append((f, -1, str(e)))

print("\n========== Summary ==========")
print(f"Available: {len(available)}")
for email in available:
    print(f"  ✅ {email}")
print(f"\nFailed: {len(failed)}")
for email, code, err in failed:
    print(f"  ❌ {email} - {code}: {err[:80]}")
