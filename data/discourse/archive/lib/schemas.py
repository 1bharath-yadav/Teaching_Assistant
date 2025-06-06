"""Schema definitions for Discourse Typesense collections."""

DISCOURSE_SCHEMA = {
    "name": "discourse_posts",
    "description": "Discourse posts to embed and index",
    "fields": [
        {"name": "topic_id", "type": "string"},
        {"name": "topic_title", "type": "string"},
        {"name": "content", "type": "string"},
        {"name": "url", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "embedding", "type": "float[]", "num_dim": 1536},
    ],
}
