import os
import json
import copy
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
import typesense
from typesense.exceptions import ObjectNotFound
from openai import OpenAI
from itertools import islice

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://aipipe.org/openai/v1"
)

typesense_client = typesense.Client({
    'nodes': [{'host': 'localhost', 'port': '8108', 'protocol': 'http'}],
    'api_key': os.getenv("TYPESENSE_API_KEY") or "conscious-field",
    'connection_timeout_seconds': 10
})

# Constants
DATA_DIR = Path("/home/archer/projects/llm_tests/Teaching_Assistant/data/data")
JSON_FILE = DATA_DIR / "processed_topics.json"
DISCOURSE_COLLECTION = "discourse_posts"

MODULES_BASE_DIR = Path("/home/archer/projects/llm_tests/Teaching_Assistant/data/tools-in-data-science-public")
MODULES = [
    "development_tools", "deployment_tools", "large_language_models",
    "data_sourcing", "data_preparation", "data_analysis", "data_visualization",
    "project-1", "project-2", "misc"
]

# Schemas
DISCOURSE_SCHEMA = {
    "name": DISCOURSE_COLLECTION,
    "fields": [
        {"name": "topic_id", "type": "string"},
        {"name": "topic_title", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "url", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "embedding", "type": "float[]", "num_dim": 1536}
    ]
}

CHAPTERS_SCHEMA = {
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "embedding", "type": "float[]", "num_dim": 1536}
    ]
}

# ----------- Core Functions -----------

def create_collection(name: str, schema: Dict) -> None:
    schema_with_name = copy.deepcopy(schema)
    schema_with_name["name"] = name
    try:
        typesense_client.collections[name].retrieve()
        print(f"Collection {name} already exists.")
    except ObjectNotFound:
        typesense_client.collections.create(schema_with_name)
        print(f"Created collection {name}.")

def generate_embedding(text: str) -> List[float]:
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def index_discourse_posts(posts: List[Dict]) -> None:
    texts = [post["content"] for post in posts]
    embeddings = batch_generate_embeddings(texts)

    jsonl_data = []
    for post, embedding in zip(posts, embeddings):
        if not embedding:
            print(f"Skipping post {post['topic_id']} due to embedding error.")
            continue
        document = {
            "topic_id": post["topic_id"],
            "topic_title": post["topic_title"],
            "content": post["content"],
            "url": post["url"],
            "timestamp": post["timestamp"],
            "embedding": embedding
        }
        jsonl_data.append(json.dumps(document))
    
    if jsonl_data:
        if jsonl_data:
            documents = [json.loads(doc) for doc in jsonl_data]
            batch_upsert_documents(COLLECTION_NAME, documents)
            print(f"Indexed {len(documents)} posts in {COLLECTION_NAME}.")


def index_module_chunks(module: str) -> None:
    collection_name = module
    create_collection(collection_name, CHAPTERS_SCHEMA)

    chunks_file = MODULES_BASE_DIR / module / "chunks.json"
    if not chunks_file.exists():
        print(f"No chunks.json found in {module}")
        return

    with open(chunks_file, 'r') as f:
        chunks = json.load(f)

    texts = [chunk["content"] for chunk in chunks]
    embeddings = batch_generate_embeddings(texts)

    batched_documents = []

    for chunk, embedding in zip(chunks, embeddings):
        if not embedding:
            print(f"Skipping chunk {chunk['id']} due to embedding error.")
            continue

        document = {
            "id": chunk["id"],
            "content": chunk["content"],
            "embedding": embedding
        }

        batched_documents.append(document)

    # Batch upsert to Typesense
    batch_upsert_documents(collection_name, batched_documents)
    print(f"Indexed {len(batched_documents)} chunks in {collection_name}")



# ----------- Orchestration -----------

def process_discourse_posts() -> None:
    if not JSON_FILE.exists():
        print(f"No {JSON_FILE} found.")
        return
    create_collection(DISCOURSE_COLLECTION, DISCOURSE_SCHEMA)
    try:
        with open(JSON_FILE, 'r') as f:
            posts = json.load(f)
        if posts:
            index_discourse_posts(posts)
        else:
            print("No posts found in JSON.")
    except Exception as e:
        print(f"Error reading {JSON_FILE}: {e}")

def process_module_chunks() -> None:
    for module in MODULES:
        index_module_chunks(module)


# --- New: Batched Embedding Function ---

def batch_generate_embeddings(texts: List[str], batch_size: int = 1) -> List[List[float]]:
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            embeddings.extend([[] for _ in batch])  # Empty embeddings for failed ones
    return embeddings

#    ------- Batch Upsert Function -------
def batch_upsert_documents(collection_name: str, documents: List[Dict], batch_size: int = 1) -> None:
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        jsonl_batch = [json.dumps(doc) for doc in batch]
        try:
            response = typesense_client.collections[collection_name].documents.import_(
                jsonl_batch, {'action': 'upsert'}
            )
            for res in response:
                if not res["success"]:
                    print(f"Error indexing document {res['document'].get('id', 'unknown')}: {res['error']}")
        except Exception as e:
            print(f"Batch indexing error in {collection_name}: {e}")


def main():
    process_discourse_posts()
    process_module_chunks()

if __name__ == "__main__":
    main()
