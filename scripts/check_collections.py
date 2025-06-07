#!/usr/bin/env python3
# filepath: /home/archer/projects/llm_tests/Teaching_Assistant/scripts/check_collections.py
"""
Check Typesense collections using the project's configuration.
This script lists all collections in the Typesense instance.
"""

import os
import sys
import json

# Add the project root to path so we can import from lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from the config module
from lib.config import get_typesense_client


def main():
    """Check Typesense collections and print information."""
    try:
        # Create a client with the known working API key
        import typesense

        client = typesense.Client(
            {
                "api_key": "xyz",  # Hardcoded API key that works
                "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
                "connection_timeout_seconds": 10,
            }
        )

        # List all collections
        collections = client.collections.retrieve()

        if not collections:
            print("No collections found in Typesense.")
            return

        print(f"Found {len(collections)} collections:")

        # Print collection details
        for collection in collections:
            print(f"\nCollection: {collection['name']}")
            print(
                f"  - Number of documents: {collection.get('num_documents', 'unknown')}"
            )
            print(f"  - Created at: {collection.get('created_at', 'unknown')}")

            # Print schema information
            fields = collection.get("fields", [])
            if fields:
                print("  - Fields:")
                for field in fields:
                    print(
                        f"    - {field.get('name', 'unknown')}: {field.get('type', 'unknown')}"
                    )

    except Exception as e:
        print(f"Error accessing Typesense: {e}")


if __name__ == "__main__":
    main()
