#!/usr/bin/env python3
"""
Quick API Test for Smart Search Router Integration

Test the main API endpoint to ensure it uses the smart router correctly.
"""

import asyncio
import requests
import json
import time

def test_api_endpoint():
    """Test the main API endpoint with the smart router"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API Endpoint with Smart Search Router")
    print("=" * 50)
    
    # Test questions to verify different scenarios
    test_questions = [
        "What is web scraping?",
        "How do I use Docker for deployment?",
        "What are LLMs and how do I use them?",
        "How do I handle missing data in pandas?",
        "What's the best way to visualize data?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: '{question}'")
        print("-" * 40)
        
        payload = {
            "question": question
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/api/v1/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                links = result.get("links", [])
                
                print(f"✅ Success! ({response_time:.2f}s)")
                print(f"   Answer length: {len(answer)} chars")
                print(f"   Sources: {len(sources) if sources else 0}")
                print(f"   Links: {len(links) if links else 0}")
                
                # Show preview of answer
                preview = answer[:100] + "..." if len(answer) > 100 else answer
                print(f"   Preview: {preview}")
                
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print(f"\n🎉 API endpoint test completed!")

def test_health_check():
    """Test the health check endpoint"""
    
    print(f"\n🔍 Testing Health Check Endpoint")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed!")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Service: {health_data.get('service', 'unknown')}")
            
            config_info = health_data.get('configuration', {})
            print(f"   Chat provider: {config_info.get('chat_provider', 'unknown')}")
            print(f"   Search provider: {config_info.get('search_provider', 'unknown')}")
            print(f"   Hybrid search: {config_info.get('hybrid_search_enabled', 'unknown')}")
            
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🚀 Starting API Test...")
    print("Make sure the API server is running on http://localhost:8000")
    print()
    
    test_health_check()
    test_api_endpoint()
