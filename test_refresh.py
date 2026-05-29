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
ok = []
refresh_fail = []

for f in os.listdir(auth_dir):
    if not f.endswith(".json"):
        continue
    path = os.path.join(auth_dir, f)
    with open(path, "r") as handle:
        acc = json.load(handle)
    email = acc["email"]
    print(f"Testing {email}...")
    r = requests.post(API_URL, headers=headers, json=data, timeout=30)
    if r.status_code == 200:
        print(f"✅ {email} - OK (request succeeded)")
        ok.append(email)
    else:
        err = r.json().get("error", {}).get("message", r.text)
        print(f"❌ {email} - {r.status_code}: {err[:100]}")
        if "refresh" in err.lower() or "invalid" in err.lower() or "401" in str(r.status_code):
            refresh_fail.append((email, r.status_code, err))

print("\n========== Refresh Test Summary ==========")
print(f"Total: {len(ok) + len(refresh_fail)}")
print(f"✅ OK: {len(ok)}")
for e in ok:
    print(f"  {e}")
print(f"\n❌ Refresh/Token failed: {len(refresh_fail)}")
for e, code, err in refresh_fail:
    print(f"  {e} - {code}: {err[:80]}")
