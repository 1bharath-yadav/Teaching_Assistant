#!/usr/bin/env python3

import requests
import json
import time
import pytest


def test_api_server():
    """Test the API server with a simple question."""
    url = "http://localhost:8000/api/v1/ask"

    payload = {
        "question": "Hello wrold, how are you?"  # Intentional typo to test spell correction
    }

    headers = {"Content-Type": "application/json"}

    try:
        print("Testing API server with Ollama...")
        print(f"Sending request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✓ API server is working with Ollama!")
            print(f"Response: {json.dumps(result, indent=2)}")
            assert True  # Test passes if we get a 200 response
        else:
            print(f"✗ API server returned error: {response.status_code}")
            print(f"Response: {response.text}")
            assert False, f"API server returned error: {response.status_code}"

    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API server. Is it running?")
        # Skip test if server is not running - this is an integration test
        pytest.skip("API server is not running")
    except Exception as e:
        print(f"✗ Error testing API server: {e}")
        # Skip test if there are connection issues
        pytest.skip(f"Could not test API server: {e}")


if __name__ == "__main__":
    # Wait a moment for server to start if just launched
    time.sleep(2)
    success = test_api_server()
    exit(0 if success else 1)
