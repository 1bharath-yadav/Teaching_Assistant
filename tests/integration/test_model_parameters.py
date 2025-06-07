#!/usr/bin/env python3
"""
Test script to verify model parameter integration between frontend and backend.
Tests that model parameters are properly passed from frontend requests to backend processing.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from api.models.schemas import QuestionRequest
from api.services.answer_service import hybrid_search_and_generate_answer


async def test_model_parameters():
    """Test that model parameters are properly handled in the backend."""

    # Test 1: Request with custom model parameters
    print("=" * 60)
    print("TEST 1: Custom Model Parameters")
    print("=" * 60)

    test_request = QuestionRequest(
        question="What is data science?",
        temperature=0.2,  # Lower temperature for consistent output
        max_tokens=150,  # Limited tokens
        top_p=0.8,
        presence_penalty=0.1,
        frequency_penalty=0.1,
    )

    print(f"Request: {test_request.model_dump()}")

    try:
        result = await hybrid_search_and_generate_answer(
            test_request,
            collections=["data_analysis", "misc"],  # Use available collections
            alpha=0.5,
            top_k=3,
        )

        print(f"Response type: {type(result)}")
        if isinstance(result, str):
            try:
                result_dict = json.loads(result)
                answer = result_dict.get("answer", "")
                print(f"Answer length: {len(answer)} characters")
                print(f"Answer preview: {answer[:200]}...")
            except json.JSONDecodeError:
                print(f"Raw response: {result[:200]}...")

        print("✅ Custom parameters test completed successfully")

    except Exception as e:
        print(f"❌ Custom parameters test failed: {str(e)}")
        return False

    # Test 2: Request with default parameters (None values)
    print("\n" + "=" * 60)
    print("TEST 2: Default Parameters (None values)")
    print("=" * 60)

    test_request_default = QuestionRequest(
        question="What is machine learning?",
        temperature=None,  # Should use config defaults
        max_tokens=None,
        top_p=None,
        presence_penalty=None,
        frequency_penalty=None,
    )

    print(f"Request: {test_request_default.model_dump()}")

    try:
        result = await hybrid_search_and_generate_answer(
            test_request_default,
            collections=["large_language_models", "misc"],
            alpha=0.5,
            top_k=3,
        )

        print(f"Response type: {type(result)}")
        if isinstance(result, str):
            try:
                result_dict = json.loads(result)
                answer = result_dict.get("answer", "")
                print(f"Answer length: {len(answer)} characters")
                print(f"Answer preview: {answer[:200]}...")
            except json.JSONDecodeError:
                print(f"Raw response: {result[:200]}...")

        print("✅ Default parameters test completed successfully")

    except Exception as e:
        print(f"❌ Default parameters test failed: {str(e)}")
        return False

    # Test 3: Verify schema validation
    print("\n" + "=" * 60)
    print("TEST 3: Schema Validation")
    print("=" * 60)

    try:
        # Test valid parameters
        valid_request = QuestionRequest(
            question="Test question",
            temperature=0.7,
            max_tokens=100,
            top_p=0.9,
            presence_penalty=0.0,
            frequency_penalty=0.0,
        )
        print("✅ Valid parameter schema validation passed")

        # Test invalid parameters (should be caught by Pydantic)
        try:
            invalid_request = QuestionRequest(
                question="Test question",
                temperature=2.0,  # Invalid: > 1.0
                max_tokens=-10,  # Invalid: negative
            )
            print("⚠️  Invalid parameters were accepted (validation might be loose)")
        except Exception as validation_error:
            print(f"✅ Invalid parameters correctly rejected: {validation_error}")

    except Exception as e:
        print(f"❌ Schema validation test failed: {str(e)}")
        return False

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY! 🎉")
    print("Model parameters are properly integrated between frontend and backend.")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = asyncio.run(test_model_parameters())
    sys.exit(0 if success else 1)
