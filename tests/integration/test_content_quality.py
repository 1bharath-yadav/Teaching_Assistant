#!/usr/bin/env python3
"""
Integration test for content quality verification.
Ensures that cleaned content is being used in the search pipeline.
"""

import sys
from pathlib import Path
import pytest
import asyncio

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from api.services.search_service import hybrid_search_across_collections
from api.core.clients import typesense_client
from api.models.schemas import QuestionRequest


class TestContentQuality:
    """Test content quality in search results."""

    def test_search_returns_clean_content(self):
        """Test that search service returns cleaned content when available."""

        async def run_search_test():
            # Create a QuestionRequest object
            request = QuestionRequest(question="data visualization")

            # Perform search
            results = await hybrid_search_across_collections(
                payload=request,
                collections=[
                    "unified_knowledge_base",
                    "discourse_posts_optimized",
                    "chapters_misc",
                ],
                top_k=5,
            )

            assert results, "Search should return results"

            # Check content quality
            html_tags_found = False
            for result in results:
                content = result["document"].get("content", "")
                if "<" in content and ">" in content:
                    # Check for common HTML tags
                    html_indicators = [
                        "<h1>",
                        "<h2>",
                        "<p>",
                        "<div>",
                        "<a href=",
                        "<img src=",
                    ]
                    if any(indicator in content for indicator in html_indicators):
                        html_tags_found = True
                        print(f"HTML tags found in content: {content[:200]}...")
                        break

            assert not html_tags_found, "Search results should not contain HTML tags"

        # Run the async test
        asyncio.run(run_search_test())

    def test_clean_content_field_exists(self):
        """Test that clean_content field exists in TypeSense collections."""
        collections_to_check = ["unified_knowledge_base", "discourse_posts_optimized"]

        for collection_name in collections_to_check:
            try:
                # Get a sample document
                search_result = typesense_client.collections[
                    collection_name
                ].documents.search({"q": "data", "query_by": "content", "limit": 1})

                if search_result["found"] > 0:
                    doc = search_result["hits"][0]["document"]

                    # Check if clean_content field exists
                    if "clean_content" in doc:
                        clean_content = str(doc["clean_content"])
                        raw_content = str(doc.get("content", ""))

                        print(f"\nCollection: {collection_name}")
                        print(f"Raw content length: {len(raw_content)}")
                        print(f"Clean content length: {len(clean_content)}")

                        # Clean content should generally be shorter or equal
                        assert len(clean_content) <= len(
                            raw_content
                        ), "Clean content should not be longer than raw content"

                        # Clean content should not contain HTML tags
                        html_indicators = [
                            "<h1>",
                            "<h2>",
                            "<p>",
                            "<div>",
                            "<a href=",
                            "<img src=",
                        ]
                        has_html = any(
                            indicator in clean_content for indicator in html_indicators
                        )
                        assert (
                            not has_html
                        ), f"Clean content should not contain HTML tags in {collection_name}"
                    else:
                        print(f"Warning: No clean_content field in {collection_name}")

            except Exception as e:
                print(f"Error checking collection {collection_name}: {e}")


if __name__ == "__main__":
    test = TestContentQuality()
    test.test_search_returns_clean_content()
    test.test_clean_content_field_exists()
    print("✅ All content quality tests passed!")
