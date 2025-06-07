#!/usr/bin/env python3
# filepath: /home/archer/projects/llm_tests/Teaching_Assistant/scripts/simple_collection_checker.py
"""
A simplified script to check Typesense collections.
"""

import subprocess
import json

def main():
    """Check collections using the curl command."""
    try:
        # Use curl to get collections with the known working API key
        cmd = ['curl', '-s', '-H', 'X-TYPESENSE-API-KEY: xyz', 'http://localhost:8108/collections']
        result = subprocess.check_output(cmd, text=True)
        
        # Parse the JSON response
        collections = json.loads(result)
        
        if not collections:
            print("No collections found in Typesense.")
            return
            
        print(f"Found {len(collections)} collections:")
        
        # Print collection details
        for collection in collections:
            print(f"\nCollection: {collection['name']}")
            print(f"  - Number of documents: {collection.get('num_documents', 'unknown')}")
            print(f"  - Created at: {collection.get('created_at', 'unknown')}")
            
            # Print schema information
            fields = collection.get('fields', [])
            if fields:
                print("  - Fields:")
                for field in fields:
                    print(f"    - {field.get('name', 'unknown')}: {field.get('type', 'unknown')}")
    
    except Exception as e:
        print(f"Error accessing Typesense: {e}")
        
if __name__ == "__main__":
    main()
