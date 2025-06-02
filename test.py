import typesense
import json
from typesense.exceptions import TypesenseClientError
from typing import List, Dict

typesense_client = typesense.Client({ # type: ignore
    'nodes': [{'host': 'localhost', 'port': '8108', 'protocol': 'http'}], # type: ignore
    'api_key': "conscious-field",
    'connection_timeout_seconds': 10
})

docs = typesense_client.collections["discourse_posts"].documents.search({
    "q": "*",
    "query_by": "topic_title",
    "per_page": 10
})
print(json.dumps(docs, indent=2))
