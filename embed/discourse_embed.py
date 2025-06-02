import copy
import json
import typesense
from pathlib import Path
from openai import OpenAI
from typing import List, Dict
from typesense.exceptions import TypesenseClientError
from dotenv import load_dotenv
import os

load_dotenv() 

openai_api_key = os.getenv("OPENAI_API_KEY")
typesense_api_key = os.getenv("TYPESENSE_API_KEY")

typesense_client = typesense.Client({ # type: ignore
    'nodes': [{'host': 'localhost', 'port': '8108', 'protocol': 'http'}], # type: ignore
    'api_key': "conscious-field",
    'connection_timeout_seconds': 10
})



openai_client = OpenAI(api_key=openai_api_key, base_url="https://aipipe.org/openai/v1") # type: ignore

# Files to be processed
DATA_DIR = Path("/home/archer/projects/llm_tests/Teaching_Assistant/data/data")
JSON_FILE = DATA_DIR / "processed_topics.json"
COLLECTION_NAME = "discourse_posts"

# Typesense schema for discourse_posts collection
DISCOURSE_SCHEMA = {
    "name": COLLECTION_NAME,
    "fields": [
        {"name": "topic_id", "type": "string"},
        {"name": "topic_title", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "url", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "embedding", "type": "float[]", "num_dim": 1536}
    ]
}

#Create the Typesense collection if it doesn't exist.
def create_collection() -> None:
    try:
        typesense_client.collections[COLLECTION_NAME].retrieve()
        print(f"Collection {COLLECTION_NAME} already exists.")
    except typesense.exceptions.ObjectNotFound:
        typesense_client.collections.create(DISCOURSE_SCHEMA)
        print(f"Created collection {COLLECTION_NAME}.")

#Generate embedding for text using OpenAI
def generate_embedding(text: str) -> List[float]:
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding for text: {e}")
        return []
   
#Index posts with embeddings in Typesense.

def index_posts(posts: List[Dict]) -> None:
    jsonl_data = []
    for post in posts:
        embedding = generate_embedding(post["content"])
        print(f"Generated embedding for post {post['topic_id']}.")
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
        try:
            response = typesense_client.collections[COLLECTION_NAME].documents.import_(jsonl_data, {'action': 'upsert'})
            print(f"Indexed {len(jsonl_data)} posts in {COLLECTION_NAME}.")
            for res in response:
                if not res["success"]:
                    print(f"Error indexing post {res['document']['topic_id']}: {res['error']}")
        except Exception as e:
            print(f"Error indexing to {COLLECTION_NAME}: {e}")


#Process processed_topics.json and index in Typesense.





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
    schema = copy.deepcopy(chapters_schema) 
    schema["name"] = collection_name
    try:
        typesense_client.collections.create(schema)
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
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk["content"]
            )
        embedding = response.data[0].embedding


        # Prepare document for Typesense
        document = {
            "id": chunk["id"],
            "content": chunk["content"],
            "embedding": embedding
        }

        # Index in Typesense
        try:
            typesense_client.collections[collection_name].documents.create(document)
            print(f"Indexed {chunk['id']} in {collection_name}")
        except Exception as e:
            print(f"Error indexing {chunk['id']}: {e}")



def main():
    if not JSON_FILE.exists():
        print(f"No {JSON_FILE} found. Exiting.")
        return
    
    # Create collection
    create_collection()
    
    # Read processed_topics.json
    try:
        with open(JSON_FILE, 'r') as f:
            posts = json.load(f)
    except Exception as e:
        print(f"Error reading {JSON_FILE}: {e}")
        return
    
    # Index posts
    if posts:
        index_posts(posts)
    else:
        print(f"No posts found in {JSON_FILE}.")

if __name__ == "__main__":
    main()