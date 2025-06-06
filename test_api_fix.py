#!/usr/bin/env python3
"""
Test script to verify the API endpoint works with the fix
"""

import requests
import json


def test_api():
    print("=== Testing API Endpoint ===\n")

    url = "http://localhost:8000/api/v1/ask"
    payload = {"question": "how llm extraction works"}

    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(url, json=payload, timeout=30)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Success! Response:")
            print(f"  Answer preview: {result.get('answer', '')[:200]}...")
            print(f"  Sources: {result.get('sources', 'N/A')}")
            print(f"  Links: {result.get('links', 'N/A')}")
        else:
            print(f"Error response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    test_api()
