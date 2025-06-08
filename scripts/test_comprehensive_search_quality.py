#!/usr/bin/env python3
"""
Test script to verify search results contain cleaned content by testing
different types of queries to find various content types.
"""

import sys
import os
import asyncio
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.models.schemas import QuestionRequest
from api.services.search_service import hybrid_search_across_collections


async def test_content_quality_comprehensive():
    """Test search with various queries to find different types of content"""

    print("🔍 Comprehensive Search Content Quality Test")
    print("=" * 60)

    # Different test queries to find various content types
    test_queries = [
        "machine learning model deployment",
        "data visualization with matplotlib",
        "python programming examples",
        "project assignment submission",
        "SQL database queries",
    ]

    all_collections = [
        "discourse_posts_optimized",
        "unified_knowledge_base",
        "chapters_misc",
        "chapters_data_analysis",
        "chapters_development_tools",
    ]

    total_results = 0
    total_html_found = 0

    for query in test_queries:
        print(f"\n🔎 Testing Query: '{query}'")
        print("-" * 40)

        payload = QuestionRequest(question=query)

        try:
            results = await hybrid_search_across_collections(
                payload=payload, collections=all_collections, top_k=3
            )

            query_html_count = 0

            for i, result in enumerate(results, 1):
                document = result.get("document", {})
                content = document.get("content", "")
                collection = result.get("collection", "unknown")

                # Check for HTML tags
                html_indicators = [
                    "<h1>",
                    "<h2>",
                    "<h3>",
                    "<p>",
                    "<div>",
                    "<a href=",
                    "<img src=",
                    "<aside class=",
                    "<blockquote>",
                    "<code>",
                    "<pre>",
                ]
                contains_html = any(tag in content for tag in html_indicators)

                if contains_html:
                    query_html_count += 1
                    total_html_found += 1
                    print(f"  ❌ Result {i} ({collection}): Contains HTML")
                    # Show which HTML tags were found
                    found_tags = [tag for tag in html_indicators if tag in content]
                    print(f"     HTML tags found: {found_tags[:3]}...")
                else:
                    print(f"  ✅ Result {i} ({collection}): Clean content")

                # Show content sample
                content_sample = content[:150].replace("\n", " ").strip()
                print(f"     Sample: {content_sample}...")

            total_results += len(results)
            print(
                f"  📊 Query results: {len(results)} total, {query_html_count} with HTML"
            )

        except Exception as e:
            print(f"  ❌ Error with query '{query}': {e}")

    # Final summary
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE CONTENT QUALITY RESULTS:")
    print(f"Total Results Tested: {total_results}")
    print(f"Results with HTML tags: {total_html_found}")
    print(f"Results with clean content: {total_results - total_html_found}")
    print(
        f"Clean content rate: {((total_results - total_html_found) / total_results * 100):.1f}%"
        if total_results > 0
        else "No results"
    )

    if total_html_found == 0 and total_results > 0:
        print("🎉 PERFECT: All search results use cleaned content!")
        return True
    elif total_results == 0:
        print("⚠️  No results found for testing")
        return False
    else:
        print(f"⚠️  WARNING: {total_html_found} results still contain HTML tags")
        return False


async def test_before_after_comparison():
    """Test to show what the content looked like before vs after cleaning"""

    print("\n" + "=" * 60)
    print("🔬 Before/After Content Comparison")
    print("=" * 60)

    payload = QuestionRequest(question="programming tutorial")

    try:
        results = await hybrid_search_across_collections(
            payload=payload, collections=["discourse_posts_optimized"], top_k=2
        )

        if results:
            for i, result in enumerate(results, 1):
                document = result.get("document", {})

                # Check if both fields exist
                if "clean_content" in document and "content" in document:
                    clean_content = document["clean_content"]
                    raw_content = document.get(
                        "content", ""
                    )  # This might be the same as clean now

                    print(f"\nDocument {i} Analysis:")
                    print(f"ID: {document.get('id', 'unknown')}")
                    print(f"Content length: {len(raw_content)} chars")
                    print(f"Clean content length: {len(clean_content)} chars")

                    # Show first 300 chars of each
                    print(f"\nCurrent content (first 300 chars):")
                    print(f"'{raw_content[:300]}...'")

                    if clean_content != raw_content:
                        print(f"\nClean content (first 300 chars):")
                        print(f"'{clean_content[:300]}...'")
                        print("✅ Content fields are different - cleaning is working")
                    else:
                        print(
                            "ℹ️  Content fields are identical - this document was already clean"
                        )

    except Exception as e:
        print(f"❌ Error in comparison: {e}")


async def main():
    """Run comprehensive content quality tests"""

    print("🧪 Comprehensive Search Service Content Quality Test")
    print("Testing multiple queries and collections to verify cleaned content...")
    print()

    # Test with various queries
    success = await test_content_quality_comprehensive()

    # Compare content fields
    await test_before_after_comparison()

    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS: Search service is consistently returning cleaned content!")
        print("   The fix has resolved the HTML content issue.")
    else:
        print("❌ Some issues found with content quality.")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
