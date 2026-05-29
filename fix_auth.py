#!/usr/bin/env python3
import json
import os

auth_dir = "/home/cpa/CLIProxyAPI/auths"

for f in os.listdir(auth_dir):
    if not f.endswith(".json"):
        continue
    path = os.path.join(auth_dir, f)
    with open(path, "r") as fobj:
        data = json.load(fobj)
    if "type" not in data:
        data["type"] = "codex"
        with open(path, "w") as fobj:
            json.dump(data, fobj, indent=2)
        print(f"Fixed {f}")
print("Done.")
