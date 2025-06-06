#!/usr/bin/env python3
"""
Test script to verify the full search pipeline works correctly
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.services.search_service import hybrid_search_across_collections
from api.models.schemas import QuestionRequest

async def test_search():
    print("=== Testing Full Search Pipeline ===\n")
    
    # Test the same question that was failing
    payload = QuestionRequest(question="how llm extraction works")
    collections = ['chapters_data_sourcing', 'chapters_deployment_tools']
    
    print(f"Question: {payload.question}")
    print(f"Collections to search: {collections}")
    print()
    
    try:
        # Perform the search
        results = await hybrid_search_across_collections(
            payload=payload,
            collections=collections,
            alpha=0.7,
            top_k=5
        )
        
        print(f"Search Results:")
        print(f"  Number of results: {len(results)}")
        
        if results:
            print("\n  First few results:")
            for i, result in enumerate(results[:3]):
                doc = result.get('document', {})
                content_preview = doc.get('content', '')[:100] + "..." if len(doc.get('content', '')) > 100 else doc.get('content', '')
                collection = result.get('collection', 'unknown')
                text_match = result.get('text_match', 0)
                vector_distance = result.get('vector_distance', 'N/A')
                
                print(f"    Result {i+1}:")
                print(f"      Collection: {collection}")
                print(f"      Text Match Score: {text_match}")
                print(f"      Vector Distance: {vector_distance}")
                print(f"      Content Preview: {content_preview}")
                print()
        else:
            print("  No results found")
            
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_search())
