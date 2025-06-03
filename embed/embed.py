import json
from pathlib import Path
from lib import (
    create_collection,
    DISCOURSE_SCHEMA,
    CHAPTERS_SCHEMA,  # MODULE COLLECTIONSA ARE CREATED AT INDEXING.PY
    index_discourse_posts,
    index_module_chunks,
)

# Configuration
DATA_DIR = Path("/home/archer/projects/llm_tests/Teaching_Assistant/data")
MODULES_BASE_DIR = Path(
    "/home/archer/projects/llm_tests/Teaching_Assistant/data/chapters/tools-in-data-science-public"
)
POSTS_JSON_FILE = DATA_DIR / "discourse" / "processed_topics.json"
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


def process_discourse_posts() -> None:
    """Process and index discourse posts."""
    if not POSTS_JSON_FILE.exists():
        print(f"No {POSTS_JSON_FILE} found.")
        return

    create_collection(DISCOURSE_COLLECTION, DISCOURSE_SCHEMA)
    try:
        with open(POSTS_JSON_FILE, "r") as f:
            posts = json.load(f)
        if posts:
            index_discourse_posts(posts)
        else:
            print("No posts found in JSON.")
    except Exception as e:
        print(f"Error reading {POSTS_JSON_FILE}: {e}")


def process_module_chunks() -> None:
    """Process and index module chunks."""
    for module in MODULES:
        index_module_chunks(module, MODULES_BASE_DIR)


def main():
    process_discourse_posts()
    process_module_chunks()


if __name__ == "__main__":
    main()
