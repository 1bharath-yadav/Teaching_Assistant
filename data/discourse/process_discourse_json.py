import json
import datetime
import os
from typing import List, Dict, Any
import html2text

try:
    import tiktoken
except ImportError:
    tiktoken = None


def clean_content(html_content: str) -> str:
    """Convert HTML content to plain text."""
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    return h.handle(html_content).strip()


def chunk_content(
    content: str, topic_id: int, max_tokens: int = 4096
) -> List[Dict[str, Any]]:
    """Chunk content into pieces under max_tokens, returning a list of partial documents."""
    if tiktoken is None:
        print("tiktoken not available. Treating each post as a chunk.")
        posts = content.split(" | ")
        return [
            {"content": post.strip(), "chunk_id": f"{topic_id}_{i+1}"}
            for i, post in enumerate(posts)
            if post.strip()
        ]

    encoding = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoding.encode(content)

    if len(tokens) <= max_tokens:
        return [{"content": content, "chunk_id": str(topic_id)}]

    chunks = []
    current_chunk = ""
    current_tokens = 0
    posts = content.split(" | ")

    for post in posts:
        post_tokens = len(encoding.encode(post))
        if current_tokens + post_tokens > max_tokens:
            if current_chunk:
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "chunk_id": f"{topic_id}_{len(chunks)+1}",
                    }
                )
                current_chunk = ""
                current_tokens = 0
        current_chunk += post + " | "
        current_tokens += post_tokens

    if current_chunk:
        chunks.append(
            {
                "content": current_chunk.strip(),
                "chunk_id": f"{topic_id}_{len(chunks)+1}",
            }
        )

    return chunks


def process_json(input_file: str, output_file: str, max_tokens: int = 4096) -> None:
    """Process the scraped JSON file and write individual cleaned posts as JSONL."""
    # Read input JSON
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        print(f"Input file {input_file} not found.")
        return

    output_dir = os.path.dirname(output_file)
    if output_dir:  # Only create directory if there's a path
        os.makedirs(output_dir, exist_ok=True)
    count = 0

    output_data = []

    for post in posts:
        try:
            topic_id = post["topic_id"]
            post_number = post.get("post_number", 1)
            username = post.get("username", "unknown")
            raw_content = post.get("post_content", "")
            if not raw_content:
                continue

            # Clean HTML
            cleaned_content = clean_content(raw_content)

            # Timestamp
            created_at = datetime.datetime.strptime(
                post["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            timestamp = created_at.strftime("%Y-%m-%d")

            # Full content with context
            content = f"Post {post_number} by {username}:\n{cleaned_content}"

            # Chunk if necessary
            chunks = chunk_content(content, topic_id, max_tokens)

            for chunk in chunks:
                record = {
                    "topic_id": f"{topic_id}_{post_number}",
                    "topic_title": post["topic_title"],
                    "content": chunk["content"],
                    "url": f"https://discourse.onlinedegree.iitm.ac.in/t/{topic_id}",
                    "timestamp": timestamp,
                    "username": username,
                }
                output_data.append(record)
                count += 1

        except Exception as e:
            print(f"Skipping post due to error: {e}")

    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {count} documents to {output_file}")


if __name__ == "__main__":
    INPUT_FILE = "scraped_posts.json"
    OUTPUT_FILE = "processed_topics.json"
    MAX_TOKENS = 4096
    process_json(INPUT_FILE, OUTPUT_FILE, MAX_TOKENS)
