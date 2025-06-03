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

def chunk_content(content: str, topic_id: int, max_tokens: int = 4096) -> List[Dict[str, Any]]:
    """Chunk content into pieces under max_tokens, returning a list of partial documents."""
    if tiktoken is None:
        print("tiktoken not available. Treating each post as a chunk.")
        posts = content.split(' | ')
        return [{"content": post.strip(), "chunk_id": f"{topic_id}_{i+1}"} for i, post in enumerate(posts) if post.strip()]
    
    encoding = tiktoken.encoding_for_model('gpt-4o')
    tokens = encoding.encode(content)
    
    if len(tokens) <= max_tokens:
        return [{"content": content, "chunk_id": str(topic_id)}]
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    posts = content.split(' | ')
    
    for post in posts:
        post_tokens = len(encoding.encode(post))
        if current_tokens + post_tokens > max_tokens:
            if current_chunk:
                chunks.append({"content": current_chunk.strip(), "chunk_id": f"{topic_id}_{len(chunks)+1}"})
                current_chunk = ""
                current_tokens = 0
        current_chunk += post + " | "
        current_tokens += post_tokens
    
    if current_chunk:
        chunks.append({"content": current_chunk.strip(), "chunk_id": f"{topic_id}_{len(chunks)+1}"})
    
    return chunks

def process_json(input_file: str, output_file: str, max_tokens: int = 4096) -> None:
    """Process the scraped JSON file to consolidate posts by topic and chunk content."""
    # Read input JSON
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    except FileNotFoundError:
        print(f"Input file {input_file} not found.")
        return
    
    # Group posts by topic_id
    topics = {}
    for post in posts:
        topic_id = post['topic_id']
        if topic_id not in topics:
            topics[topic_id] = {
                'topic_title': post['topic_title'],
                'posts': [],
                'timestamp': post['created_at']
            }
        topics[topic_id]['posts'].append(post)
    
    # Process topics
    output_data = []
    for topic_id, topic_data in topics.items():
        # Sort posts by post_number
        sorted_posts = sorted(topic_data['posts'], key=lambda x: x.get('post_number', 1))
        
        # Concatenate post content
        content_parts = []
        for post in sorted_posts:
            if not post.get('post_content'):
                continue
            cleaned_content = clean_content(post['post_content'])
            content_parts.append(f"Post {post['post_number']}: {cleaned_content}")
        content = " | ".join(content_parts)
        
        # Simplify timestamp
        created_at = datetime.datetime.strptime(topic_data['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        timestamp = created_at.strftime('%Y-%m-%d')
        
        # Construct URL
        url = f"https://discourse.onlinedegree.iitm.ac.in/t/{topic_id}"
        
        # Chunk content if necessary
        chunks = chunk_content(content, topic_id, max_tokens)
        
        # Create documents for each chunk
        for chunk in chunks:
            output_data.append({
                'topic_id': f"{chunk['chunk_id']}",
                'topic_title': topic_data['topic_title'],
                'content': chunk['content'],
                'url': url,
                'timestamp': timestamp
            })
    
    # Save output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(output_data)} documents to {output_file}")

if __name__ == "__main__":
    INPUT_FILE = "data/scraped_posts.json"
    OUTPUT_FILE = "data/processed_topics.json"
    MAX_TOKENS = 4096
    process_json(INPUT_FILE, OUTPUT_FILE, MAX_TOKENS)