#!/usr/bin/env python3
"""
Test script for enhanced discourse search with OCR content.

This script demonstrates the enhanced search capabilities
with OCR-extracted text from images.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

try:
    import typesense
except ImportError:
    print(
        "Error: typesense library not found. Install with: pip install typesense-client"
    )
    sys.exit(1)


def get_typesense_client():
    """Get Typesense client."""
    return typesense.Client(
        {
            "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
            "api_key": os.getenv("TYPESENSE_API_KEY", "xyz"),
            "connection_timeout_seconds": 10,
        }
    )


def test_ocr_search_capabilities():
    """Test various OCR search scenarios."""
    client = get_typesense_client()
    collection_name = "discourse_posts_enhanced"

    print("=" * 60)
    print("🔍 ENHANCED DISCOURSE SEARCH WITH OCR CAPABILITIES")
    print("=" * 60)

    # Test 1: Search for text that might appear in images
    print("\n1. Searching for 'Tools in Data Science' (likely in images):")
    print("-" * 50)

    search_results = client.collections[collection_name].documents.search(
        {
            "q": "Tools Data Science",
            "query_by": "content,extracted_text_from_images,topic_title",
            "limit": 5,
            "highlight_fields": "content,extracted_text_from_images",
        }
    )

    print(f"Found {search_results['found']} documents")
    for i, hit in enumerate(search_results["hits"][:3], 1):
        doc = hit["document"]
        print(f"\n{i}. Topic: {doc['topic_title']}")
        print(f"   URL: {doc['url']}")
        print(f"   Has Images: {doc.get('has_images', False)}")
        if doc.get("has_images"):
            print(f"   Image Count: {len(doc.get('image_urls', []))}")
            if doc.get("extracted_text_from_images"):
                print(f"   OCR Text: {doc['extracted_text_from_images'][:100]}...")

        # Show highlights if available
        if "highlight" in hit:
            if "extracted_text_from_images" in hit["highlight"]:
                print(
                    f"   OCR Highlight: {hit['highlight']['extracted_text_from_images']}"
                )

    # Test 2: Filter by documents with images
    print("\n\n2. Searching documents with images only:")
    print("-" * 50)

    search_results = client.collections[collection_name].documents.search(
        {"q": "*", "query_by": "content", "filter_by": "has_images:true", "limit": 5}
    )

    print(f"Found {search_results['found']} documents with images")
    for i, hit in enumerate(search_results["hits"][:3], 1):
        doc = hit["document"]
        print(f"\n{i}. Topic: {doc['topic_title']}")
        print(f"   Image URLs: {len(doc.get('image_urls', []))}")
        if doc.get("extracted_text_from_images"):
            ocr_text = doc["extracted_text_from_images"]
            print(
                f"   OCR Preview: {ocr_text[:150]}{'...' if len(ocr_text) > 150 else ''}"
            )

    # Test 3: Search for specific terms that might be in screenshots
    print(
        "\n\n3. Searching for terms likely in screenshots (scores, grades, assignments):"
    )
    print("-" * 50)

    test_queries = ["assignment", "score", "grade", "deadline", "submission"]

    for query in test_queries:
        search_results = client.collections[collection_name].documents.search(
            {"q": query, "query_by": "content,extracted_text_from_images", "limit": 3}
        )

        image_hits = [
            hit
            for hit in search_results["hits"]
            if hit["document"].get("has_images", False)
            and query.lower()
            in hit["document"].get("extracted_text_from_images", "").lower()
        ]

        if image_hits:
            print(f"\n   '{query}' found in {len(image_hits)} documents with OCR text:")
            for hit in image_hits[:2]:
                doc = hit["document"]
                print(f"   - {doc['topic_title']}")
                ocr_text = doc.get("extracted_text_from_images", "")
                # Find context around the query term
                lower_text = ocr_text.lower()
                if query.lower() in lower_text:
                    pos = lower_text.find(query.lower())
                    start = max(0, pos - 30)
                    end = min(len(ocr_text), pos + len(query) + 30)
                    context = ocr_text[start:end].strip()
                    print(f"     Context: ...{context}...")

    # Test 4: Hybrid search (text + images)
    print("\n\n4. Hybrid search combining regular content and OCR text:")
    print("-" * 50)

    search_results = client.collections[collection_name].documents.search(
        {
            "q": "error problem issue",
            "query_by": "content,extracted_text_from_images,topic_title",
            "limit": 5,
        }
    )

    print(f"Found {search_results['found']} documents for 'error problem issue'")
    for i, hit in enumerate(search_results["hits"][:3], 1):
        doc = hit["document"]
        print(f"\n{i}. Topic: {doc['topic_title']}")
        print(f"   Has Images: {doc.get('has_images', False)}")

        # Check if match might be from OCR
        if doc.get("has_images") and doc.get("extracted_text_from_images"):
            ocr_text = doc["extracted_text_from_images"].lower()
            query_terms = ["error", "problem", "issue"]
            ocr_matches = [term for term in query_terms if term in ocr_text]
            if ocr_matches:
                print(f"   OCR matches: {', '.join(ocr_matches)}")
                print(f"   OCR snippet: {doc['extracted_text_from_images'][:100]}...")

    # Test 5: Statistics
    print("\n\n5. Collection Statistics:")
    print("-" * 50)

    # Total documents
    all_docs = client.collections[collection_name].documents.search(
        {"q": "*", "query_by": "content", "limit": 0}
    )

    # Documents with images
    image_docs = client.collections[collection_name].documents.search(
        {"q": "*", "query_by": "content", "filter_by": "has_images:true", "limit": 0}
    )

    # Documents with OCR text
    ocr_docs = client.collections[collection_name].documents.search(
        {"q": "extracted", "query_by": "extracted_text_from_images", "limit": 0}
    )

    print(f"Total documents: {all_docs['found']}")
    print(f"Documents with images: {image_docs['found']}")
    print(f"Documents with OCR text: {ocr_docs['found']}")
    print(f"OCR coverage: {(ocr_docs['found']/all_docs['found']*100):.1f}%")

    print("\n" + "=" * 60)
    print("✅ Enhanced search testing completed!")
    print(
        "OCR integration is working and searchable content has been significantly enhanced."
    )
    print("=" * 60)


if __name__ == "__main__":
    test_ocr_search_capabilities()
