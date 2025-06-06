#!/usr/bin/env python3
"""
Test script to verify the classification service fix
"""

import asyncio
from api.services.classification_service import classify_question
from api.models.schemas import QuestionRequest

async def test_classification():
    # Test the same question that was failing
    payload = QuestionRequest(question="how llm extraction works")
    
    result = await classify_question(payload)
    
    print("Classification result:")
    print(f"  Question: {result['question']}")
    print(f"  Collections: {result['collections']}")
    print(f"  Collections type: {type(result['collections'])}")
    
    # Check if it's properly a flat list
    if isinstance(result['collections'], list) and all(isinstance(item, str) for item in result['collections']):
        print("✓ Collections format is correct (flat list of strings)")
    else:
        print("✗ Collections format is incorrect")

if __name__ == "__main__":
    asyncio.run(test_classification())
