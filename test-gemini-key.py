#!/usr/bin/env python3
import requests
import json
import sys

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
if not API_KEY:
    print("Usage: python test-gemini-key.py <api_key>")
    sys.exit(1)

# Test Gemini API
url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [
        {
            "role": "user",
            "parts": [{"text": "Say hello this is a test."}]
        }
    ]
}

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ API Key works! Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("\n❌ Request failed:")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
