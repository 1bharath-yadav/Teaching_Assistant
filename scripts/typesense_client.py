import os
import sys

# Add the project root to path so we can import from lib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from the config module
from lib.config import get_typesense_client

# Get a properly configured Typesense client using project settings
client = get_typesense_client()

# List all collections
collections = client.collections.retrieve()

# Print collection names
for collection in collections:
    print(collection["name"])
