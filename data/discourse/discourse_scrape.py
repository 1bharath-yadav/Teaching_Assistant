
import requests
import json
import datetime
import time
from typing import List, Dict, Any
import os

def load_cookies_from_json(json_file: str, target_domain: str) -> Dict[str, str]:
    with open(json_file, 'r') as f:
        cookie_data = json.load(f)
    
    cookies = {}
    for entry in cookie_data:
        if entry.get("domain") == target_domain and entry.get("name") and entry.get("value"):
            cookies[entry["name"]] = entry["value"]
    return cookies

def create_authenticated_session(cookies: Dict[str, str], domain: str) -> requests.Session:
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value, domain=domain)
    
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": f"https://{domain}",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    })
    return session

def fetch_topics(session: requests.Session, base_url: str, category_id: int, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Dict[str, Any]]:
    """Fetch topics from a category within the specified date range."""
    topics = []
    page = 0
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    while True:
        url = f"{base_url}/c/{category_id}.json?page={page}"
        response = session.get(url)
        
        if response.status_code != 200:
            print(f"Failed to fetch topics on page {page}: {response.status_code}")
            break
        
        data = response.json()
        topic_list = data.get('topic_list', {}).get('topics', [])
        if not topic_list:
            break
        
        for topic in topic_list:
            created_at = datetime.datetime.strptime(topic['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
            created_timestamp = int(created_at.timestamp())
            if start_timestamp <= created_timestamp <= end_timestamp:
                topics.append(topic)
        
        page += 1
        time.sleep(1)  # Respectful delay to avoid rate limiting
    
    return topics

def fetch_topic_posts(session: requests.Session, base_url: str, topic_id: int) -> List[Dict[str, Any]]:
    """Fetch all posts for a given topic."""
    posts = []
    url = f"{base_url}/t/{topic_id}.json"
    response = session.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch posts for topic {topic_id}: {response.status_code}")
        return posts
    
    data = response.json()
    posts_stream = data.get('post_stream', {}).get('posts', [])
    posts.extend(posts_stream)
    
    return posts

def save_data(data: List[Dict[str, Any]], output_file: str) -> None:
    """Save scraped data to a JSON file."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # Constants
    DISCOURSE_DOMAIN = "discourse.onlinedegree.iitm.ac.in"
    DISCOURSE_URL = f"https://{DISCOURSE_DOMAIN}"
    CATEGORY_ID = 34  # TDS category ID
    OUTPUT_FILE = "data/scraped_posts.json"
    
    # Date range
    START_DATE = datetime.datetime(2025, 1, 1)
    END_DATE = datetime.datetime(2025, 4, 14)
    
    # Load cookies and create session BTW get cookies.json from browser

    try:
        cookies = load_cookies_from_json("cookie.json", DISCOURSE_DOMAIN)
    except FileNotFoundError:
        print("cookie.json not found. Please provide valid cookies.")
        return
    
    session = create_authenticated_session(cookies, DISCOURSE_DOMAIN)
    
    # Test login
    response = session.get(f"{DISCOURSE_URL}/session/current.json")
    if response.status_code == 200:
        user_data = response.json()
        print(f"Authenticated as: {user_data['current_user']['username']}")
    else:
        print("Authentication failed")
        print("Status:", response.status_code)
        print("Response:", response.text)
        return
    
    # Fetch topics
    print(f"Fetching topics from category {CATEGORY_ID} between {START_DATE} and {END_DATE}...")
    topics = fetch_topics(session, DISCOURSE_URL, CATEGORY_ID, START_DATE, END_DATE)
    print(f"Retrieved {len(topics)} topics.")
    
    # Fetch posts for each topic
    all_posts = []
    for topic in topics:
        topic_id = topic['id']
        topic_title = topic['title']
        print(f"Fetching posts for topic {topic_id}: {topic_title}")
        posts = fetch_topic_posts(session, DISCOURSE_URL, topic_id)
        
        for post in posts:
            all_posts.append({
                'topic_id': topic_id,
                'topic_title': topic_title,
                'post_id': post['id'],
                'post_content': post.get('cooked', ''),
                'created_at': post.get('created_at', ''),
                'username': post.get('username', ''),
                'post_number': post.get('post_number', 1)
            })
        time.sleep(1)  # Respectful delay
    
    # Save data
    print(f"Saving {len(all_posts)} posts to {OUTPUT_FILE}...")
    save_data(all_posts, OUTPUT_FILE)
    print("Scraping complete.")

if __name__ == "__main__":
    main()