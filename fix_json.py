#!/usr/bin/env python3
import re

INPUT_FILE = "/root/.openclaw/workspace/AI-Account-Toolkit/openai_register/accounts.json"
OUTPUT_FILE = "/root/.openclaw/workspace/accounts_fixed.json"

with open(INPUT_FILE, "r") as f:
    content = f.read()

# 把 "{\n  " 变成 "{ "，让每个对象占一行
fixed = re.sub(r'{\n\s+', '{ ', content)
# 把换行的 "} 变成 }\n"，分隔每个对象
fixed = re.sub(r'\}\n\s+', '}\n', fixed)
# 处理最后一个
fixed = re.sub(r'\}\s*$', '}\n', fixed)

with open(OUTPUT_FILE, "w") as f:
    f.write(fixed)

lines = fixed.strip().split('\n')
print(f"Fixed done. {len(lines)} accounts extracted.")
