"""Schema definitions for Chapters Typesense collections."""

CHAPTERS_SCHEMA = {
    "name": "chapters",
    "description": "Chapters from various modules to embed and index",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "embedding", "type": "float[]", "num_dim": 1536},
    ],
}
