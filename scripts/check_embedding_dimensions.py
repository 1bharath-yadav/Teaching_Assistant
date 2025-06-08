#!/usr/bin/env python3
"""
Check the actual embedding dimensions in TypeSense collections.
"""

import os
import sys
import json
import typesense

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def main():
    """Check embedding dimensions in TypeSense collections."""
    try:
        # Create TypeSense client
        client = typesense.Client(
            {
                "api_key": "xyz",
                "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
                "connection_timeout_seconds": 10,
            }
        )

        # Get all collections
        collections = client.collections.retrieve()
        
        print("Checking embedding dimensions in TypeSense collections:\n")
        
        for collection in collections:
            collection_name = collection['name']
            if not collection_name:  # Skip empty collection names
                continue
                
            print(f"Collection: {collection_name}")
            print(f"  Documents: {collection.get('num_documents', 0)}")
            
            # Check the schema for embedding field details
            fields = collection.get('fields', [])
            embedding_field = None
            for field in fields:
                if field.get('name') == 'embedding':
                    embedding_field = field
                    break
            
            if embedding_field:
                field_type = embedding_field.get('type', 'unknown')
                print(f"  Embedding field type: {field_type}")
                
                # Try to get a sample document to check actual embedding dimensions
                try:
                    # Search for any document in this collection
                    search_result = client.collections[collection_name].documents.search({
                        'q': '*',
                        'query_by': 'content',
                        'per_page': 1
                    })
                    
                    if search_result.get('hits') and len(search_result['hits']) > 0:
                        doc = search_result['hits'][0]['document']
                        if 'embedding' in doc:
                            embedding = doc['embedding']
                            if isinstance(embedding, list):
                                dimensions = len(embedding)
                                print(f"  Actual embedding dimensions: {dimensions}")
                                
                                # Check if it matches expected dimensions
                                if dimensions == 1536:
                                    print(f"  ⚠️  Using OpenAI dimensions (1536)")
                                elif dimensions == 768:
                                    print(f"  ✅ Using Ollama dimensions (768)")
                                else:
                                    print(f"  ❓ Unknown embedding dimensions ({dimensions})")
                            else:
                                print(f"  Embedding is not a list: {type(embedding)}")
                        else:
                            print(f"  No embedding field found in document")
                    else:
                        print(f"  No documents found to check dimensions")
                        
                except Exception as e:
                    print(f"  Error checking documents: {e}")
            else:
                print(f"  No embedding field found in schema")
            
            print()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
