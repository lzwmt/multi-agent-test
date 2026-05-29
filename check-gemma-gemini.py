#!/usr/bin/env python3
import requests
import json
import sys

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
MODELS_TO_TEST = [
    "gemma-2-9b-it",
    "gemma-2-27b-it", 
    "gemma-3-1b-it",
    "gemma-3-4b-it",
    "gemma-3-12b-it",
    "gemma-3-27b-it",
]

if not API_KEY:
    print("Usage: python check-gemma-gemini.py <api_key>")
    sys.exit(1)

print(f"Testing API Key: {API_KEY[:8]}...{API_KEY[-4:]}\n")

for model in MODELS_TO_TEST:
    full_model = f"models/{model}"
    url = f"https://generativelanguage.googleapis.com/v1/{full_model}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "What is 2+2?"}]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 10
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
                    print(f"✅ Success! Answer: {text.strip()}")
        elif response.status_code == 429:
            data = response.json()
            error = data.get("error", {})
            print(f"❌ 429 Quota exceeded: {error.get('message', '')[:150]}")
        elif response.status_code == 404:
            print("❌ 404 Not Found - model doesn't exist on this API endpoint")
        else:
            print(f"❌ Failed: {response.text[:150]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
