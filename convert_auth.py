#!/usr/bin/env python3
import json
import os

INPUT_FILE = "/root/.openclaw/workspace/accounts_fixed.json"
OUTPUT_DIR = "/home/cpa/CLIProxyAPI/auths"

os.makedirs(OUTPUT_DIR, exist_ok=True)

count = 0
with open(INPUT_FILE, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            acc = json.loads(line)
        except Exception as e:
            print(f"Invalid line: {e}")
            continue
        
        # CLIProxyAPI format
        from datetime import datetime
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
        
        # filename: {email_username}.json
        email = acc["email"]
        username = email.split("@")[0]
        filename = f"{username}.json"
        out_path = os.path.join(OUTPUT_DIR, filename)
        
        with open(out_path, "w") as out_f:
            json.dump(cp_auth, out_f, indent=2)
        
        count += 1
        print(f"Converted {filename}")

print(f"\nDone. Converted {count} accounts.")
