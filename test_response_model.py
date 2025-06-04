#!/usr/bin/env python3
"""
Test script to verify the QuestionResponse model fixes
"""

import json
import sys
from pathlib import Path

# Add the api directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "api"))

from process import QuestionResponse, LinkObject


def test_question_response_model():
    """Test the QuestionResponse model with different input formats"""

    print("Testing QuestionResponse model...")

    # Test 1: Basic response with string sources
    try:
        response1 = QuestionResponse(
            answer="This is a test answer",
            sources=["https://example.com", "https://test.com"],
            links=None,
        )
        print("✅ Test 1 passed: Basic response with string sources")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")

    # Test 2: Response with structured links
    try:
        response2 = QuestionResponse(
            answer="This is another test answer",
            sources=["https://example.com"],
            links=[
                LinkObject(url="https://example.com", text="Example Link"),
                LinkObject(url="https://test.com", text="Test Link"),
            ],
        )
        print("✅ Test 2 passed: Response with structured links")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")

    # Test 3: Response with no links/sources
    try:
        response3 = QuestionResponse(
            answer="Answer with no links", sources=None, links=None
        )
        print("✅ Test 3 passed: Response with no links/sources")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

    # Test 4: Simulate the actual data format from OpenAI
    try:
        # This is what was causing the original error
        openai_links = [
            {
                "url": "https://www.tableau.com/learn/articles/data-visualization",
                "text": "What is Data Visualization? - Tableau",
            },
            {
                "url": "https://www.data-to-viz.com/",
                "text": "Data Visualization Resources",
            },
        ]

        # Convert to proper format
        link_objects = [LinkObject(**link) for link in openai_links]
        source_strings = [link["url"] for link in openai_links]

        response4 = QuestionResponse(
            answer="Data visualization is the graphical representation of information and data.",
            sources=source_strings,
            links=link_objects,
        )
        print("✅ Test 4 passed: OpenAI-style response conversion")
        print(f"   - Answer length: {len(response4.answer)}")
        print(
            f"   - Number of sources: {len(response4.sources) if response4.sources else 0}"
        )
        print(f"   - Number of links: {len(response4.links) if response4.links else 0}")

    except Exception as e:
        print(f"❌ Test 4 failed: {e}")

    print("\nAll tests completed!")


def test_json_serialization():
    """Test JSON serialization of the response"""
    print("\nTesting JSON serialization...")

    try:
        response = QuestionResponse(
            answer="Test answer",
            sources=["https://example.com"],
            links=[LinkObject(url="https://example.com", text="Example")],
        )

        # Convert to dict (this is what FastAPI does)
        response_dict = response.model_dump()

        # Convert to JSON
        json_str = json.dumps(response_dict, indent=2)

        print("✅ JSON serialization successful")
        print("Sample JSON output:")
        print(json_str)

    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")


if __name__ == "__main__":
    test_question_response_model()
    test_json_serialization()
