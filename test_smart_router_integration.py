#!/usr/bin/env python3
"""
Test Smart Search Router Integration

This script tests the smart search router with all three strategies
to ensure the configuration and integration works properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.models.schemas import QuestionRequest
from api.services.smart_search_router import SmartSearchRouter
from lib.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_router_integration():
    """Test the smart router integration with different strategies"""

    print("🧪 Testing Smart Search Router Integration")
    print("=" * 50)

    # Load configuration
    try:
        config = get_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   Current strategy: {config.hybrid_search.search_strategy}")
        print(
            f"   Available strategies: {list(config.hybrid_search.strategies.__dict__.keys())}"
        )
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    # Initialize router
    try:
        router = SmartSearchRouter()
        print(f"✅ Smart router initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize router: {e}")
        return False

    # Test questions
    test_questions = [
        "What is web scraping and how do I use APIs?",
        "How do I use Docker for deployment?",
        "What are the best practices for data visualization?",
        "How do I work with large language models?",
        "What is the difference between supervised and unsupervised learning?",
    ]

    # Test each strategy
    strategies = ["unified", "enhanced", "classification"]

    for strategy in strategies:
        print(f"\n🔍 Testing {strategy.upper()} strategy:")
        print("-" * 30)

        # Check if strategy is enabled
        strategy_config = getattr(config.hybrid_search.strategies, strategy)
        if not strategy_config.enabled:
            print(f"⚠️  {strategy} strategy is disabled in configuration")
            continue

        total_time = 0
        total_results = 0

        for i, question in enumerate(test_questions, 1):
            try:
                payload = QuestionRequest(question=question)

                # Force specific strategy for testing
                result = await router.search(payload, force_strategy=strategy)

                search_time = result["metadata"]["search_time"]
                result_count = result["metadata"]["result_count"]

                total_time += search_time
                total_results += result_count

                print(f"   {i}. '{question[:40]}...'")
                print(f"      Results: {result_count}, Time: {search_time:.3f}s")

            except Exception as e:
                print(f"   ❌ Error with question {i}: {e}")

        avg_time = total_time / len(test_questions)
        avg_results = total_results / len(test_questions)

        print(
            f"   📊 Summary: Avg time: {avg_time:.3f}s, Avg results: {avg_results:.1f}"
        )

    # Test strategy comparison
    print(f"\n🆚 Testing strategy comparison:")
    print("-" * 30)

    test_payload = QuestionRequest(
        question="How do I use Docker for machine learning projects?"
    )

    try:
        comparison_result = await router.compare_strategies(test_payload)
        print("✅ Strategy comparison completed:")

        for strategy, data in comparison_result.get("strategies", {}).items():
            if "results" in data:
                results = data["metadata"]["result_count"]
                time_taken = data["metadata"]["search_time"]
                print(f"   {strategy}: {results} results in {time_taken:.3f}s")
            elif "error" in data:
                print(f"   {strategy}: Error - {data['error']}")

    except Exception as e:
        print(f"❌ Strategy comparison failed: {e}")

    # Performance statistics
    print(f"\n📈 Performance Statistics:")
    print("-" * 30)

    stats = router.get_performance_stats()
    performance_by_strategy = stats.get("performance_by_strategy", {})
    for strategy, data in performance_by_strategy.items():
        if data["total_calls"] > 0:
            avg_time = data["average_response_time"]
            avg_results = data["average_results"]
            total_calls = data["total_calls"]
            print(
                f"   {strategy}: {total_calls} calls, {avg_time:.3f}s avg, {avg_results:.1f} results avg"
            )

    print(f"\n🎉 Integration test completed successfully!")
    return True


async def test_config_switching():
    """Test dynamic strategy switching via configuration"""

    print(f"\n🔄 Testing Configuration-Based Strategy Switching")
    print("=" * 50)

    config = get_config()
    original_strategy = config.hybrid_search.search_strategy

    print(f"Original strategy: {original_strategy}")

    # Test payload
    payload = QuestionRequest(question="What is the best way to handle missing data?")

    strategies_to_test = ["unified", "enhanced", "classification"]

    for strategy in strategies_to_test:
        print(f"\n🔧 Testing with strategy: {strategy}")

        # Temporarily change strategy in config
        config.hybrid_search.search_strategy = strategy

        try:
            router = SmartSearchRouter()  # New router with updated config
            result = await router.search(payload)

            strategy_used = result["metadata"]["strategy_used"]
            search_time = result["metadata"]["search_time"]
            result_count = result["metadata"]["result_count"]

            print(f"   ✅ Strategy used: {strategy_used}")
            print(f"   📊 Results: {result_count}, Time: {search_time:.3f}s")

            if strategy_used != strategy:
                print(f"   ⚠️  Expected {strategy}, but used {strategy_used}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Restore original strategy
    config.hybrid_search.search_strategy = original_strategy
    print(f"\n🔄 Restored original strategy: {original_strategy}")


if __name__ == "__main__":
    asyncio.run(test_router_integration())
    asyncio.run(test_config_switching())
