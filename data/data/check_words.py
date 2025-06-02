import json
import html2text
import re
from typing import Set

def clean_content(html_content: str) -> str:
    """Convert HTML content to plain text."""
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    return h.handle(html_content).strip()

def get_words(text: str) -> Set[str]:
    """Extract unique words from text, ignoring case and punctuation."""
    # Convert to lowercase and replace newlines with spaces
    text = text.lower().replace('\n', ' ')
    # Tokenize words (split on whitespace and punctuation)
    words = re.findall(r'\b\w+\b', text)
    return set(words)

def check_words(scraped_file: str, processed_file: str) -> None:
    """Check if all words in scraped_posts.json are in processed_topics.json."""
    # Read scraped_posts.json
    try:
        with open(scraped_file, 'r', encoding='utf-8') as f:
            scraped_posts = json.load(f)
    except FileNotFoundError:
        print(f"File {scraped_file} not found.")
        return
    
    # Read processed_topics.json
    try:
        with open(processed_file, 'r', encoding='utf-8') as f:
            processed_topics = json.load(f)
    except FileNotFoundError:
        print(f"File {processed_file} not found.")
        return
    
    # Extract words from scraped_posts.json
    scraped_words = set()
    for post in scraped_posts:
        if not post.get('post_content'):
            continue
        cleaned_content = clean_content(post['post_content'])
        scraped_words.update(get_words(cleaned_content))
    
    # Extract words from processed_topics.json
    processed_words = set()
    for topic in processed_topics:
        if not topic.get('content'):
            continue
        processed_words.update(get_words(topic['content']))
    
    # Check if all scraped words are in processed words
    missing_words = scraped_words - processed_words
    
    if missing_words:
        print(f"Missing words ({len(missing_words)}): {sorted(missing_words)}")
    else:
        print("All words from scraped_posts.json are present in processed_topics.json.")

if __name__ == "__main__":
    SCRAPED_FILE = "scraped_posts.json"
    PROCESSED_FILE = "processed_topics.json"
    check_words(SCRAPED_FILE, PROCESSED_FILE)