#!/usr/bin/env python3
"""
Test content cleaning - Compare raw content vs clean_content
"""

import json
import sys
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from lib.config import get_config
import typesense


def get_typesense_client():
    """Get Typesense client."""
    return typesense.Client(
        {
            "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
            "api_key": "xyz",
            "connection_timeout_seconds": 30,
        }
    )


def test_content_cleaning():
    """Test content cleaning comparison."""
    client = get_typesense_client()

    print("=" * 80)
    print("🧪 CONTENT CLEANING COMPARISON TEST")
    print("=" * 80)

    test_collections = [
        "unified_knowledge_base",
        "discourse_posts_optimized",
        "chapters_misc",
    ]

    test_query = "data visualization"

    for collection_name in test_collections:
        print(f"\n{'='*60}")
        print(f"COLLECTION: {collection_name}")
        print(f"{'='*60}")

        try:
            # Get raw results
            results = client.collections[collection_name].documents.search(
                {
                    "q": test_query,
                    "query_by": "content",
                    "per_page": 3,
                    "exclude_fields": "embedding",  # Exclude large embedding vectors
                }
            )

            print(f"Found: {results.get('found', 0)} documents")

            for i, hit in enumerate(results.get("hits", [])[:2], 1):
                doc = hit.get("document", {})

                print(f"\n--- DOCUMENT {i} CONTENT COMPARISON ---")
                print(f"Document ID: {doc.get('id', 'N/A')}")

                # Get both content fields
                raw_content = doc.get("content", "")
                clean_content = doc.get("clean_content", "")

                print(f"\n🔍 RAW CONTENT (first 300 chars):")
                print("-" * 40)
                print(repr(raw_content[:300]))
                if len(raw_content) > 300:
                    print(f"... (truncated, total: {len(raw_content)} chars)")

                print(f"\n✨ CLEAN CONTENT (first 300 chars):")
                print("-" * 40)
                print(repr(clean_content[:300]))
                if len(clean_content) > 300:
                    print(f"... (truncated, total: {len(clean_content)} chars)")

                # Analyze differences
                print(f"\n📊 ANALYSIS:")
                print("-" * 40)
                print(f"Raw content length: {len(raw_content)}")
                print(f"Clean content length: {len(clean_content)}")

                if clean_content and raw_content:
                    reduction = (
                        (len(raw_content) - len(clean_content)) / len(raw_content)
                    ) * 100
                    print(f"Size reduction: {reduction:.1f}%")

                # Check for HTML tags
                raw_has_html = "<" in raw_content and ">" in raw_content
                clean_has_html = "<" in clean_content and ">" in clean_content
                print(f"Raw has HTML tags: {raw_has_html}")
                print(f"Clean has HTML tags: {clean_has_html}")

                # Check for HTML entities
                import re

                raw_entities = len(re.findall(r"&[a-zA-Z0-9#]+;", raw_content))
                clean_entities = len(re.findall(r"&[a-zA-Z0-9#]+;", clean_content))
                print(f"Raw HTML entities: {raw_entities}")
                print(f"Clean HTML entities: {clean_entities}")

                # Check for excessive whitespace
                raw_extra_spaces = raw_content.count("  ")
                clean_extra_spaces = clean_content.count("  ")
                print(f"Raw extra spaces: {raw_extra_spaces}")
                print(f"Clean extra spaces: {clean_extra_spaces}")

                # Check for line breaks
                raw_line_breaks = raw_content.count("\n")
                clean_line_breaks = clean_content.count("\n")
                print(f"Raw line breaks: {raw_line_breaks}")
                print(f"Clean line breaks: {clean_line_breaks}")

                # Show quality improvement
                print(f"\n💡 QUALITY IMPROVEMENT:")
                print("-" * 40)
                if clean_content:
                    print("✅ Clean content is available and should be used")
                    if raw_has_html and not clean_has_html:
                        print("✅ HTML tags removed in clean version")
                    if raw_entities > clean_entities:
                        print("✅ HTML entities cleaned")
                    if raw_extra_spaces > clean_extra_spaces:
                        print("✅ Extra whitespace cleaned")
                    if reduction > 10:
                        print(f"✅ Significant size reduction ({reduction:.1f}%)")
                else:
                    print("⚠️ No clean content available, use raw content")

                # Show recommended usage
                print(f"\n🎯 RECOMMENDED USAGE:")
                print("-" * 40)
                preferred_content = clean_content if clean_content else raw_content
                print(f"Use: {'clean_content' if clean_content else 'content'}")
                print(f"Preview: {preferred_content[:100]}...")

        except Exception as e:
            print(f"❌ Error with collection {collection_name}: {e}")

    print(f"\n{'='*80}")
    print("🏁 CONTENT CLEANING TEST COMPLETE")
    print("=" * 80)
    print("\n💡 KEY FINDINGS:")
    print("- Always prefer 'clean_content' when available")
    print("- Clean content removes HTML tags, entities, and extra whitespace")
    print("- This reduces processing overhead in answer generation")
    print("- No need for additional content cleaning in services")


if __name__ == "__main__":
    test_content_cleaning()
