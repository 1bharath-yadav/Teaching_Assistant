#!/usr/bin/env python3
"""
Test script for streaming answer service with LangChain ChatOllama
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from api.models.schemas import QuestionRequest
from api.services.streaming_answer_service import (
    generate_streaming_answer,
    generate_answer_optimized,
)


async def test_streaming_answer():
    """Test streaming answer generation"""
    print("=" * 60)
    print("🔄 TESTING STREAMING ANSWER SERVICE")
    print("=" * 60)

    # Test question
    test_question = "How do I visualize data in Python?"

    payload = QuestionRequest(question=test_question, temperature=0.7, max_tokens=500)

    print(f"📋 Test Question: {test_question}")
    print(f"🔧 Temperature: {payload.temperature}")
    print(f"🔧 Max Tokens: {payload.max_tokens}")
    print()

    # Test streaming response
    print("🌊 STREAMING RESPONSE:")
    print("-" * 40)

    try:
        chunk_count = 0
        total_content = ""

        async for chunk in generate_streaming_answer(payload):
            chunk_data = json.loads(chunk)
            chunk_count += 1

            if chunk_data.get("type") == "chunk":
                content = chunk_data.get("content", "")
                total_content += content
                print(content, end="", flush=True)

            elif chunk_data.get("type") == "complete":
                print(f"\n\n✅ STREAMING COMPLETE!")
                print(f"📊 Total chunks: {chunk_count}")
                print(f"📏 Total content length: {len(total_content)}")
                print(
                    f"⏱️  Generation time: {chunk_data.get('generation_time', 'N/A'):.3f}s"
                )
                print(f"📚 Sources: {len(chunk_data.get('sources', []))}")

                # Show sources
                sources = chunk_data.get("sources", [])
                if sources:
                    print(f"\n📖 SOURCES:")
                    for i, source in enumerate(sources[:3], 1):
                        print(f"  {i}. {source}")

            elif chunk_data.get("type") == "error":
                print(f"\n❌ ERROR: {chunk_data.get('error', 'Unknown error')}")
                break

    except Exception as e:
        print(f"\n❌ Exception during streaming: {e}")


async def test_non_streaming_answer():
    """Test non-streaming answer generation (backward compatibility)"""
    print("\n" + "=" * 60)
    print("📝 TESTING NON-STREAMING ANSWER SERVICE")
    print("=" * 60)

    test_question = "What is Docker and how is it used in deployment?"

    payload = QuestionRequest(question=test_question, temperature=0.5)

    print(f"📋 Test Question: {test_question}")
    print(f"🔧 Temperature: {payload.temperature}")
    print()

    try:
        print("⏳ Generating answer...")
        response = await generate_answer_optimized(payload)
        response_data = json.loads(response)

        print("✅ ANSWER GENERATED!")
        print("-" * 40)
        print(response_data.get("answer", "No answer"))
        print()

        print(f"📊 Response metadata:")
        print(f"  - Answer length: {len(response_data.get('answer', ''))}")
        print(f"  - Sources: {len(response_data.get('sources', []))}")
        print(f"  - Generation time: {response_data.get('generation_time', 'N/A')}")

    except Exception as e:
        print(f"❌ Error in non-streaming test: {e}")


async def test_performance_comparison():
    """Test performance comparison between old and new approach"""
    print("\n" + "=" * 60)
    print("⚡ PERFORMANCE COMPARISON TEST")
    print("=" * 60)

    questions = [
        "How do I use Git for version control?",
        "What are the benefits of containerization?",
        "Explain machine learning model deployment",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n📋 Test {i}: {question}")
        print("-" * 50)

        payload = QuestionRequest(question=question, temperature=0.3)

        try:
            # Test optimized streaming approach
            start_time = asyncio.get_event_loop().time()

            async for chunk in generate_streaming_answer(payload):
                chunk_data = json.loads(chunk)
                if chunk_data.get("type") == "complete":
                    generation_time = chunk_data.get("generation_time", 0)
                    answer_length = len(chunk_data.get("answer", ""))
                    sources_count = len(chunk_data.get("sources", []))

                    print(f"  ✅ Optimized approach:")
                    print(f"     - Generation time: {generation_time:.3f}s")
                    print(f"     - Answer length: {answer_length} chars")
                    print(f"     - Sources used: {sources_count}")
                    break

        except Exception as e:
            print(f"  ❌ Error in optimized approach: {e}")


if __name__ == "__main__":

    async def main():
        await test_streaming_answer()
        await test_non_streaming_answer()
        await test_performance_comparison()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS COMPLETED!")
        print("=" * 60)

    asyncio.run(main())
