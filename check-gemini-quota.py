#!/usr/bin/env python3
import requests
import json
import sys

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
MODELS_TO_TEST = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001", 
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

if not API_KEY:
    print("Usage: python check-gemini-quota.py <api_key>")
    sys.exit(1)

print(f"Testing API Key: {API_KEY[:8]}...{API_KEY[-4:]}\n")

for model in MODELS_TO_TEST:
    full_model = f"models/{model}"
    url = f"https://generativelanguage.googleapis.com/v1/{full_model}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "Hi"}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 5
        }
    }
    
    print(f"=== Testing {model} ===")
    try:
        response = requests.post(url, json=payload, timeout=20)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {}).get("parts", [])
                if content:
                    text = content[0].get("text", "")
                    print(f"✅ Success! Response: {text.strip()}")
        elif response.status_code == 429:
            data = response.json()
            error = data.get("error", {})
            print(f"❌ 429 Resource Exhausted: {error.get('message', 'Quota exceeded')[:200]}...")
        else:
            print(f"❌ Failed: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
