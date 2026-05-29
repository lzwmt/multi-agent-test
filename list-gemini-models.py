#!/usr/bin/env python3
import requests
import json
import sys

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
if not API_KEY:
    print("Usage: python list-gemini-models.py <api_key>")
    sys.exit(1)

url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

try:
    response = requests.get(url, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nAvailable models:")
        for model in data.get("models", []):
            name = model.get("name", "")
            supported = model.get("supportedGenerationMethods", [])
            print(f"- {name}")
            if supported:
                print(f"  Methods: {', '.join(supported)}")
    else:
        print("\nError:")
        print(response.text)
        
except Exception as e:
    print(f"\nError: {e}")
    sys.exit(1)
