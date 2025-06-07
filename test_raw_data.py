#!/usr/bin/env python3
"""
Test script to examine raw data from Typesense collections
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

def test_raw_data_retrieval():
    """Test raw data retrieval from collections."""
    client = get_typesense_client()
    
    print("=" * 60)
    print("🔍 RAW DATA EXAMINATION FROM COLLECTIONS")
    print("=" * 60)
    
    # Test collections
    test_collections = [
        "unified_knowledge_base",
        "discourse_posts_optimized", 
        "chapters_misc"
    ]
    
    test_query = "data visualization"
    
    for collection_name in test_collections:
        print(f"\n{'='*50}")
        print(f"COLLECTION: {collection_name}")
        print(f"{'='*50}")
        
        try:
            # Get collection info
            schema = client.collections[collection_name].retrieve()
            print(f"📊 Documents: {schema.get('num_documents', 0)}")
            print(f"📋 Fields: {[f['name'] for f in schema.get('fields', [])]}")
            
            # Raw search - minimal parameters
            print(f"\n🔍 RAW SEARCH for '{test_query}':")
            print("-" * 30)
            
            raw_results = client.collections[collection_name].documents.search({
                "q": test_query,
                "query_by": "content",
                "per_page": 3,
                "highlight_full_fields": "content"
            })
            
            print(f"Found: {raw_results.get('found', 0)} documents")
            print(f"Returned: {len(raw_results.get('hits', []))} hits")
            
            # Examine raw hits structure
            for i, hit in enumerate(raw_results.get('hits', [])[:2], 1):
                print(f"\n--- HIT {i} RAW STRUCTURE ---")
                print(f"Keys in hit: {list(hit.keys())}")
                
                # Document structure
                doc = hit.get('document', {})
                print(f"Document keys: {list(doc.keys())}")
                print(f"Document ID: {doc.get('id', 'N/A')}")
                print(f"Content length: {len(doc.get('content', ''))}")
                print(f"Content preview: {doc.get('content', '')[:100]}...")
                
                # Scoring information
                print(f"Text match score: {hit.get('text_match', 'N/A')}")
                print(f"Vector distance: {hit.get('vector_distance', 'N/A')}")
                
                # Highlights
                highlights = hit.get('highlights', [])
                print(f"Highlights: {len(highlights)} items")
                if highlights:
                    for highlight in highlights[:1]:
                        print(f"  - Field: {highlight.get('field', 'N/A')}")
                        print(f"  - Snippets: {len(highlight.get('snippets', []))}")
                        if highlight.get('snippets'):
                            print(f"  - First snippet: {highlight['snippets'][0][:100]}...")
                
                # Check for unnecessary fields or processing
                print(f"\n🔧 POTENTIAL PROCESSING ISSUES:")
                unnecessary_fields = []
                for key, value in doc.items():
                    if key.startswith('_') or key in ['embedding']:
                        unnecessary_fields.append(key)
                
                if unnecessary_fields:
                    print(f"  - Potentially unnecessary fields: {unnecessary_fields}")
                else:
                    print(f"  - No obviously unnecessary fields detected")
                
                # Check content quality
                content = doc.get('content', '')
                if content:
                    has_html = '<' in content and '>' in content
                    has_special_chars = any(char in content for char in ['\\n', '\\t', '\\r'])
                    has_extra_spaces = '  ' in content
                    
                    print(f"  - Contains HTML tags: {has_html}")
                    print(f"  - Contains escape chars: {has_special_chars}")
                    print(f"  - Contains extra spaces: {has_extra_spaces}")
                    
                    if has_html or has_special_chars or has_extra_spaces:
                        print(f"  ⚠️ Content may need cleaning")
                
        except Exception as e:
            print(f"❌ Error with collection {collection_name}: {e}")
    
    print(f"\n{'='*60}")
    print("🔍 TESTING DIRECT DOCUMENT ACCESS")
    print(f"{'='*60}")
    
    # Try to get a specific document by ID
    try:
        # Get first document from unified_knowledge_base
        results = client.collections["unified_knowledge_base"].documents.search({
            "q": "*",
            "per_page": 1
        })
        
        if results.get('hits'):
            doc_id = results['hits'][0]['document']['id']
            print(f"Getting document by ID: {doc_id}")
            
            direct_doc = client.collections["unified_knowledge_base"].documents[doc_id].retrieve()
            print(f"Direct document keys: {list(direct_doc.keys())}")
            print(f"Direct document content length: {len(direct_doc.get('content', ''))}")
            print(f"Direct document content preview: {direct_doc.get('content', '')[:200]}...")
            
    except Exception as e:
        print(f"❌ Error with direct document access: {e}")

if __name__ == "__main__":
    test_raw_data_retrieval()
