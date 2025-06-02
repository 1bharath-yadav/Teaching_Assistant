import json
import typesense
import openai
from pathlib import Path

# Typesense client
client = typesense.Client({
    'nodes': [{'host': 'localhost', 'port': '8108', 'protocol': 'http'}],
    'api_key': 'your-api-key',
    'connection_timeout_seconds': 2
})


# Base directory
git_git_base_dir = Path("/home/archer/projects/llm_tests/Teaching_Assistant/data/tools-in-data-science-public")
modules = [
    "development_tools", "deployment_tools", "large_language_models",
    "data_sourcing", "data_preparation", "data_analysis", "data_visualization",
    "project-1", "project-2", "misc"
]

# Schema template
chapters_schema = {
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "embedding", "type": "float[]", "num_dim": 1536}
    ]
}

for directory in modules:
    # Create collection
    collection_name = directory
    schema = chapters_schema.copy()
    schema["name"] = collection_name
    try:
        client.collections.create(schema)
    except Exception as e:
        print(f"Collection {collection_name} already exists or error: {e}")

    # Read chunks.json
    chunks_file = git_git_base_dir / directory / "chunks.json"
    if not chunks_file.exists():
        print(f"No chunks.json in {directory}")
        continue

    with open(chunks_file, 'r') as f:
        chunks = json.load(f)

    # Generate embeddings and index
    for chunk in chunks:
        # Generate embedding
        response = openai.Embedding.create(
            model="text-embedding-3-small",  # GPT-4o-mini equivalent
            input=chunk["content"]
        )
        embedding = response["data"][0]["embedding"]

        # Prepare document for Typesense
        document = {
            "id": chunk["id"],
            "content": chunk["content"],
            "embedding": embedding
        }

        # Index in Typesense
        try:
            client.collections[collection_name].documents.create(document)
            print(f"Indexed {chunk['id']} in {collection_name}")
        except Exception as e:
            print(f"Error indexing {chunk['id']}: {e}")