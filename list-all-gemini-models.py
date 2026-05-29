#!/usr/bin/env python3
import requests
import json
import sys

API_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
if not API_KEY:
    print("Usage: python list-all-gemini-models.py <api_key>")
    sys.exit(1)

url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

try:
    response = requests.get(url, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        models = data.get("models", [])
        print(f"\nTotal {len(models)} models available:\n")
        for i, model in enumerate(sorted(models, key=lambda m: m.get("name", ""))):
            name = model.get("name", "")
            supported = model.get("supportedGenerationMethods", [])
            version = model.get("version", "N/A")
            display_name = model.get("displayName", name)
            print(f"{i+1}. {name}")
            print(f"   Display: {display_name} | Version: {version}")
            if supported:
                print(f"   Methods: {', '.join(supported)}")
            print()
    else:
        print("\nError:")
        print(response.text)
        
except Exception as e:
    print(f"\nError: {e}")
    sys.exit(1)
