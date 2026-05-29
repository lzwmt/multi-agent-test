#!/usr/bin/env python3
import json
import os
from datetime import datetime

OUTPUT_DIR = "/home/cpa/CLIProxyAPI/auths"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 读取最后一个账号信息
with open("/root/.openclaw/workspace/AI-Account-Toolkit/openai_register/accounts.json", "r") as f:
    lines = f.read().strip().split("\n")
    last_line = lines[-1]
    acc = json.loads(last_line)

# 转换格式
dt = datetime.fromisoformat(acc["expired"].replace("Z", "+00:00"))
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

with open(out_path, "w") as f:
    json.dump(cp_auth, f, indent=2)

print(f"Converted and saved to {out_path}")
print(f"Account: {acc['email']}")
print(f"Expires: {acc['expired']}")
