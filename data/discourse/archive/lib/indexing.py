import json
import sys
from pathlib import Path
from typing import Dict, List

# Add the Teaching_Assistant root directory to sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

from .client import get_typesense_client
from lib.embeddings import batch_generate_embeddings

# Constants
BATCH_SIZE = 100
DISCOURSE_COLLECTION = "discourse_posts"


def batch_upsert_documents(
    collection_name: str, documents: List[Dict], batch_size: int = BATCH_SIZE
) -> None:
    """Upsert documents to a collection in batches."""
    client = get_typesense_client()
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        jsonl_batch = [json.dumps(doc) for doc in batch]
        try:
            jsonl_string = "\n".join(jsonl_batch)
            response = client.collections[collection_name].documents.import_(
                jsonl_string, {"action": "upsert"}
            )
            print(f"Batch indexed {len(batch)} documents in {collection_name}.")
            for res_str in response:
                res = json.loads(res_str)
                if not res["success"]:
                    print(
                        f"Error indexing document {res['document'].get('id', 'unknown')}: {res['error']}"
                    )
        except Exception as e:
            print(f"Batch indexing error in {collection_name}: {e}")


def index_discourse_posts(posts: List[Dict]) -> None:
    """Index discourse posts with embeddings using the new unified embedding system."""
    texts = [post["content"] for post in posts]
    embeddings = batch_generate_embeddings(texts)

    documents = []
    for post, embedding in zip(posts, embeddings):
        if not embedding or all(x == 0.0 for x in embedding):
            print(f"Skipping post {post['topic_id']} due to embedding error.")
            continue
        document = {
            "topic_id": post["topic_id"],
            "topic_title": post["topic_title"],
            "content": post["content"],
            "url": post["url"],
            "timestamp": post["timestamp"],
            "embedding": embedding,
        }
        documents.append(document)

    if documents:
        batch_upsert_documents(DISCOURSE_COLLECTION, documents)
        print(f"Indexed {len(documents)} posts in {DISCOURSE_COLLECTION}.")
