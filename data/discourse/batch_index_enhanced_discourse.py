#!/usr/bin/env python3
"""
Batch indexing script for enhanced discourse posts with OCR data.

This script uses Typesense's batch import functionality to efficiently
index the enhanced_processed.json file with OCR content.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List
import tempfile

# Add project root to path for config access
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    import typesense
    from typesense.exceptions import ObjectNotFound, ObjectAlreadyExists
except ImportError:
    print(
        "Error: typesense library not found. Install with: pip install typesense-client"
    )
    sys.exit(1)

try:
    from lib.config import get_config

    config = get_config()
    EMBEDDING_DIMENSIONS = (
        config.embeddings.ollama.dimensions
        if config.embeddings.provider == "ollama"
        else config.embeddings.openai.dimensions
    )
except ImportError:
    print("Warning: Could not load config, using default embedding dimensions (768)")
    EMBEDDING_DIMENSIONS = 768


def get_typesense_client():
    """Get Typesense client."""
    return typesense.Client(
        {
            "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
            "api_key": os.getenv("TYPESENSE_API_KEY", "conscious-field"),
            "connection_timeout_seconds": 30,
        }
    )


def get_collection_schema(collection_name: str = "discourse_posts_enhanced") -> Dict:
    """Get the schema for enhanced discourse posts collection."""
    return {
        "name": collection_name,
        "fields": [
            {"name": "topic_id", "type": "string"},
            {"name": "topic_title", "type": "string"},
            {"name": "content", "type": "string"},
            {"name": "url", "type": "string"},
            {"name": "timestamp", "type": "string"},
            {"name": "embedding", "type": "float[]", "num_dim": EMBEDDING_DIMENSIONS},
            # Additional searchable fields
            {"name": "post_count", "type": "int32", "optional": True},
            {"name": "usernames", "type": "string[]", "facet": True, "optional": True},
            {"name": "mentions", "type": "string[]", "facet": True, "optional": True},
            {"name": "keywords", "type": "string[]", "facet": True, "optional": True},
            # Image-related fields with OCR support
            {
                "name": "image_urls",
                "type": "string[]",
                "facet": False,
                "optional": True,
            },
            {
                "name": "image_descriptions",
                "type": "string[]",
                "facet": False,
                "optional": True,
            },
            {"name": "extracted_text_from_images", "type": "string", "optional": True},
            {"name": "has_images", "type": "bool", "facet": True, "optional": True},
        ],
    }


def create_or_update_collection(client, collection_name: str) -> None:
    """Create or update the Typesense collection."""
    schema = get_collection_schema(collection_name)

    try:
        # Check if collection exists
        existing = client.collections[collection_name].retrieve()
        print(f"Collection '{collection_name}' already exists.")

        # For simplicity, we'll delete and recreate to ensure schema is current
        print(f"Deleting existing collection to ensure schema compatibility...")
        client.collections[collection_name].delete()

    except ObjectNotFound:
        print(f"Collection '{collection_name}' does not exist.")

    # Create the collection
    try:
        client.collections.create(schema)
        print(f"Successfully created collection '{collection_name}'")
    except ObjectAlreadyExists:
        print(f"Collection '{collection_name}' already exists after creation attempt")


def prepare_document_for_indexing(doc: Dict) -> Dict:
    """Prepare a document for Typesense indexing."""
    # Create a copy to avoid modifying original
    prepared_doc = doc.copy()

    # Ensure required fields exist with defaults
    defaults = {
        "post_count": 0,
        "usernames": [],
        "mentions": [],
        "keywords": [],
        "image_urls": [],
        "image_descriptions": [],
        "extracted_text_from_images": "",
        "has_images": False,
    }

    for field, default_value in defaults.items():
        if field not in prepared_doc or prepared_doc[field] is None:
            prepared_doc[field] = default_value

    # Ensure embedding is present
    if "embedding" not in prepared_doc or not prepared_doc["embedding"]:
        print(
            f"Warning: Document {prepared_doc.get('topic_id', 'unknown')} has no embedding"
        )
        prepared_doc["embedding"] = [0.0] * EMBEDDING_DIMENSIONS  # Default embedding

    # Convert topic_id to string if it's not already
    if "topic_id" in prepared_doc:
        prepared_doc["topic_id"] = str(prepared_doc["topic_id"])

    return prepared_doc


def convert_to_jsonl(documents: List[Dict], output_file: str) -> int:
    """Convert documents to JSONL format for batch import."""
    processed_count = 0

    with open(output_file, "w", encoding="utf-8") as f:
        for doc in documents:
            try:
                prepared_doc = prepare_document_for_indexing(doc)
                f.write(json.dumps(prepared_doc, ensure_ascii=False) + "\n")
                processed_count += 1
            except Exception as e:
                print(f"Error preparing document {doc.get('topic_id', 'unknown')}: {e}")
                continue

    return processed_count


def batch_index_documents(
    client, collection_name: str, jsonl_file: str, batch_size: int = 100
) -> Dict:
    """Batch index documents using Typesense import API."""
    try:
        with open(jsonl_file, "rb") as f:
            result = client.collections[collection_name].documents.import_(
                f.read(), {"batch_size": batch_size}
            )
        return result
    except Exception as e:
        print(f"Error during batch import: {e}")
        raise


def main():
    """Main function to batch index enhanced discourse data."""
    # File paths
    current_dir = Path(__file__).parent
    enhanced_file = current_dir / "enhanced_processed.json"

    if not enhanced_file.exists():
        print(f"Error: Enhanced processed file not found at {enhanced_file}")
        sys.exit(1)

    # Load enhanced processed data
    print(f"Loading enhanced processed data from {enhanced_file}")
    try:
        with open(enhanced_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
        print(f"Loaded {len(documents)} documents")
    except Exception as e:
        print(f"Error loading documents: {e}")
        sys.exit(1)

    # Get Typesense client
    client = get_typesense_client()
    collection_name = "discourse_posts_enhanced"

    # Create or update collection
    print("Creating/updating Typesense collection...")
    create_or_update_collection(client, collection_name)

    # Convert to JSONL format
    print("Converting documents to JSONL format...")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as temp_file:
        temp_jsonl_path = temp_file.name

    processed_count = convert_to_jsonl(documents, temp_jsonl_path)
    print(f"Prepared {processed_count} documents for indexing")

    # Batch index documents
    print("Starting batch indexing...")
    try:
        result = batch_index_documents(
            client, collection_name, temp_jsonl_path, batch_size=50
        )
        print("Batch indexing completed!")

        # Parse results
        if isinstance(result, list):
            success_count = 0
            error_count = 0
            for item in result:
                if item.get("success", False):
                    success_count += 1
                else:
                    error_count += 1
                    print(f"Error indexing document: {item}")

            print(f"Successfully indexed: {success_count} documents")
            if error_count > 0:
                print(f"Failed to index: {error_count} documents")
        else:
            print(f"Batch import result: {result}")

    except Exception as e:
        print(f"Error during batch indexing: {e}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_jsonl_path)
        except:
            pass

    # Verify indexing
    try:
        collection_info = client.collections[collection_name].retrieve()
        print(
            f"\nCollection '{collection_name}' now contains {collection_info['num_documents']} documents"
        )

        # Test search with OCR content
        print("\nTesting search with OCR content...")
        search_results = client.collections[collection_name].documents.search(
            {
                "q": "extracted",
                "query_by": "content,extracted_text_from_images",
                "limit": 3,
            }
        )

        print(f"Found {search_results['found']} documents containing 'extracted'")
        for hit in search_results["hits"][:2]:
            doc = hit["document"]
            print(f"- Topic: {doc['topic_title']}")
            if doc.get("has_images"):
                print(f"  Images: {len(doc.get('image_urls', []))}")
                if doc.get("extracted_text_from_images"):
                    print(f"  OCR Text: {doc['extracted_text_from_images'][:100]}...")

    except Exception as e:
        print(f"Error verifying collection: {e}")


if __name__ == "__main__":
    main()
