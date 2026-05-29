#!/usr/bin/env python3
import requests
import json
import sys

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
if not API_KEY:
    print("Usage: python test-gemini-generate.py <api_key>")
    sys.exit(1)

MODEL = "models/gemini-2.0-flash"
url = f"https://generativelanguage.googleapis.com/v1/{MODEL}:generateContent?key={API_KEY}"

payload = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "What is 2+2? Answer in one word."}]
        }
    ]
}

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Generation successful! Response:")
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                print(f"\nAnswer: {parts[0].get('text', '')}")
        print("\nFull response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("\n❌ Request failed:")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
