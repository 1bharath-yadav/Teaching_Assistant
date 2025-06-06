#!/usr/bin/env python3
"""
Test script for the updated spell check function using Ollama function tool calling.
"""

import asyncio
import sys
import os

from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.utils.spell_check import spell_check_and_correct


import pytest


@pytest.mark.asyncio
async def test_spell_check():
    """Test the spell check function with various inputs."""

    test_cases = [
        "How can I conect to the databse?",
        "Whats the best way to handel errors in python?",
        "Can you explane how to use ollama for AI?",
        "This sentance has mispelled words.",
        "Perfect spelling and grammar here.",
        "help me with api integration plese",
    ]

    print("Testing Ollama function tool calling spell check...")
    print("=" * 60)

    for i, test_input in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Original: {test_input}")

        try:
            corrected = await spell_check_and_correct(test_input)
            print(f"Corrected: {corrected}")

            if corrected != test_input:
                print("✓ Text was corrected")
            else:
                print("→ No changes needed")

        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Spell check test completed!")


if __name__ == "__main__":
    asyncio.run(test_spell_check())
