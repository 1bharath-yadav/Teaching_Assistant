import os
import sys
import json
import typesense
from typesense.exceptions import TypesenseClientError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Setup paths and client
client = typesense.Client(
    {
        "api_key": os.getenv("TYPESENSE_API_KEY") or "conscious-field",
        "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],  # type: ignore
        "connection_timeout_seconds": 5,
    }
)

DISCOURSE_COLLECTION = "discourse_posts"
MODULES = [
    "development_tools",
    "deployment_tools",
    "large_language_models",
    "data_sourcing",
    "data_preparation",
    "data_analysis",
    "data_visualization",
    "project-1",
    "project-2",
    "misc",
]


def print_sample_docs(collection_name: str, sample_size: int = 3):
    try:
        print(f"\n🔍 Checking collection: {collection_name}")
        export_data = client.collections[collection_name].documents.export()
        docs = export_data.strip().split("\n")
        print(f"✅ Total documents: {len(docs)}")

        print(f"📄 Sample {min(sample_size, len(docs))} documents:")
        for line in docs[:sample_size]:
            doc = json.loads(line)
            content_preview = doc.get("content", "")[:80].replace("\n", " ")
            print(
                f" - ID: {doc.get('id', doc.get('topic_id', 'N/A'))}, Preview: {content_preview}..."
            )
    except typesense.exceptions.ObjectNotFound:
        print(f"❌ Collection '{collection_name}' not found.")
    except Exception as e:
        print(f"⚠️  Error reading from '{collection_name}': {e}")


def main():
    print("📦 Verifying Typesense document storage\n")

    # Check Discourse posts
    print_sample_docs(DISCOURSE_COLLECTION)

    # Check module-specific collections
    for module in MODULES:
        print_sample_docs(module)


def keyword_search(
    collection_name: str, query: str, query_by: str, num_results: int = 5
) -> None:
    """Perform a keyword search on a Typesense collection and print results."""
    try:
        search_params = {
            "q": query,
            "query_by": query_by,
            "per_page": num_results,
            "sort_by": "_text_match:desc",  # Sort by relevance
        }
        response = client.collections[collection_name].documents.search(search_params)
        print(
            f"\nSearch Results for '{query}' in {collection_name} ({response['found']} total hits):"
        )
        for hit in response["hits"]:
            document = hit["document"]
            print(f"- ID: {document.get('topic_id', document.get('id', 'N/A'))}")
            if "topic_title" in document:
                print(f"  Title: {document['topic_title']}")
            print(f"  Content (snippet): {document['content'][:200]}...")
            print(f"  Score: {hit['text_match']}")
            if "url" in document:
                print(f"  URL: {document['url']}")
            print()
    except Exception as e:
        print(f"Error searching {collection_name}: {e}")


def list_collections():
    """List all collections in Typesense."""
    try:
        collections = client.collections.retrieve()
        print("Available collections:")
        for collection in collections:
            print(f"- {collection['name']}")
    except Exception as e:
        print(f"Error listing collections: {e}")


def run_keyword_search_tests():
    """Run predefined keyword search tests on all collections."""
    # Test searches for discourse_posts
    print("Testing discourse_posts collection")
    keyword_search("discourse_posts", "calendar link", "topic_title,content")
    keyword_search("discourse_posts", "course difficulty", "topic_title,content")

    # Test searches for development_tools
    print("\nTesting development_tools collection")
    keyword_search("development_tools", "FastAPI", "content")
    keyword_search("development_tools", "Docker", "content")

    # Test searches for misc
    print("\nTesting misc collection")
    keyword_search("misc", "course feedback", "content")
    keyword_search("misc", "live session", "content")


if __name__ == "__main__":
    main()

    run_keyword_search_tests()
    list_collections()
