import json
from typing import Dict, List
from pathlib import Path
from .client import get_typesense_client
from .embeddings import generate_embeddings_for_texts
from .collections import create_collection
from .schemas import CHAPTERS_SCHEMA

# Constants
BATCH_SIZE = 100


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


def index_module_chunks(module: str, modules_base_dir: Path) -> None:
    """Index chunks from a specific module using individual embedding calls."""
    collection_name = module
    create_collection(collection_name, CHAPTERS_SCHEMA)
    chunks_file = modules_base_dir / module / "chunks.json"
    if not chunks_file.exists():
        print(f"No chunks.json found in {module}")
        return

    with open(chunks_file, "r") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks from {chunks_file}")
    texts = [chunk["content"] for chunk in chunks]
    embeddings = generate_embeddings_for_texts(texts)

    documents = []
    for chunk, embedding in zip(chunks, embeddings):
        if not embedding:
            print(f"Skipping chunk {chunk['id']} due to embedding error.")
            continue
        document = {
            "id": chunk["id"],
            "content": chunk["content"],
            "embedding": embedding,
        }
        documents.append(document)

    batch_upsert_documents(collection_name, documents, BATCH_SIZE)
    print(f"Indexed {len(documents)} chunks in {collection_name}")
