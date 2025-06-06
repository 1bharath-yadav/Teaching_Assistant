#!/usr/bin/env python3
"""
Debug script to check Typesense collections and their content
"""

import json
from lib.config import get_typesense_client, get_config


def main():
    print("=== Typesense Collections Debug ===\n")

    try:
        # Get Typesense client
        client = get_typesense_client()
        config = get_config()

        print("1. Typesense Connection:")
        print(
            f"   Nodes: {[{'host': node.host, 'port': node.port, 'protocol': node.protocol} for node in config.typesense.nodes]}"
        )
        print(f"   API Key: {'***' if config.typesense.api_key else 'Not set'}")
        print()

        # List all collections
        print("2. Available Collections:")
        collections = client.collections.retrieve()
        if not collections:
            print("   No collections found!")
            return

        for collection in collections:
            name = collection["name"]
            num_documents = collection.get("num_documents", 0)
            print(f"   - {name}: {num_documents} documents")
        print()

        # Check specific collections from config
        print("3. Collections from Config:")
        print(f"   Default collections: {config.hybrid_search.default_collections}")
        print(f"   Available collections: {config.hybrid_search.available_collections}")
        print()

        # Check if the collections being searched exist
        target_collections = ["chapters_data_sourcing", "chapters_deployment_tools"]
        print(f"4. Target Collections Status:")
        collection_names = [c["name"] for c in collections]

        for target in target_collections:
            if target in collection_names:
                collection_info = next(c for c in collections if c["name"] == target)
                print(
                    f"   ✓ {target}: EXISTS with {collection_info.get('num_documents', 0)} documents"
                )

                # Get a sample document
                try:
                    result = client.collections[target].documents.search(
                        {"q": "*", "query_by": "content", "per_page": 1}
                    )
                    if result["hits"]:
                        sample_doc = result["hits"][0]["document"]
                        print(f"     Sample fields: {list(sample_doc.keys())}")
                    else:
                        print(f"     No documents found in search")
                except Exception as e:
                    print(f"     Error searching: {e}")

            else:
                print(f"   ✗ {target}: MISSING")
        print()

        # Check embedding field and schema
        print("5. Collection Schema Check:")
        for target in target_collections:
            if target in collection_names:
                try:
                    schema = client.collections[target].retrieve()
                    print(f"   {target} fields:")
                    for field in schema["fields"]:
                        field_type = field.get("type", "unknown")
                        field_name = field.get("name", "unknown")
                        print(f"     - {field_name}: {field_type}")

                        # Check if embedding field exists
                        if "embedding" in field_name.lower() or field_type == "float[]":
                            print(f"       ^ This looks like an embedding field")
                    print()
                except Exception as e:
                    print(f"   Error getting schema for {target}: {e}")

        # Test a simple search
        print("6. Test Simple Search:")
        for target in target_collections:
            if target in collection_names:
                try:
                    # Test keyword search
                    result = client.collections[target].documents.search(
                        {"q": "extraction", "query_by": "content", "per_page": 3}
                    )
                    print(
                        f"   {target} keyword search for 'extraction': {len(result['hits'])} results"
                    )

                    # Test wildcard search
                    result = client.collections[target].documents.search(
                        {"q": "*", "query_by": "content", "per_page": 3}
                    )
                    print(f"   {target} wildcard search: {len(result['hits'])} results")

                except Exception as e:
                    print(f"   Error searching {target}: {e}")

    except Exception as e:
        print(f"Error connecting to Typesense: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if Typesense is running: curl http://localhost:8108/health")
        print("2. Check if API key is correct")
        print("3. Check if collections have been created and populated")


if __name__ == "__main__":
    main()
