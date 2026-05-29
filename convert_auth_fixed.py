#!/usr/bin/env python3
import json
import os
from datetime import datetime

INPUT_FILE = "/root/.openclaw/workspace/AI-Account-Toolkit/openai_register/accounts.json"
OUTPUT_DIR = "/home/cpa/CLIProxyAPI/auths"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r") as f:
    content = f.read()

# 按 { ... } 分段提取每个JSON对象
objects = []
start = 0
balance = 0
in_str = False
escape = False

for i, c in enumerate(content):
    if c == '"' and not escape:
        in_str = not in_str
    if not in_str and c == '{':
        if balance == 0:
            start = i
        balance += 1
    if not in_str and c == '}':
        balance -= 1
        if balance == 0:
            obj_str = content[start:i+1]
            objects.append(obj_str)
    if c == '\\' and not escape:
        escape = True
    else:
        escape = False

print(f"Extracted {len(objects)} objects")

count = 0
for obj_str in objects:
    obj_str = obj_str.strip()
    if not obj_str:
        continue
    try:
        acc = json.loads(obj_str)
    except Exception as e:
        print(f"Invalid JSON: {e}")
        continue
    
    # 转换为 CLIProxyAPI 格式
    expires_str = acc["expired"]
    dt = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
    expires_at = int(dt.timestamp())
    
    cp_auth = {
        "account_id": acc["account_id"],
        "client_id": "app_EmoamEH73f0CkXAx7hrann",
        "access_token": acc["access_token"],
        "refresh_token": acc["refresh_token"],
        "expires_at": expires_at,
        "email": acc["email"]
    }
    
    email = acc["email"]
    username = email.split("@")[0]
    filename = f"{username}.json"
    out_path = os.path.join(OUTPUT_DIR, filename)
    
    with open(out_path, "w") as out_f:
        json.dump(cp_auth, out_f, indent=2)
    
    count += 1
    print(f"Converted {filename}")

print(f"\nDone. Total converted {count} accounts.")
