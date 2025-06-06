#!/usr/bin/env python3
"""
Test unified knowledge base search to verify it contains comprehensive results
"""

import asyncio
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from lib.config import get_config, get_typesense_client
from api.models.schemas import QuestionRequest

async def test_unified_search():
    """Test unified knowledge base search comprehensively"""
    
    config = get_config()
    client = get_typesense_client()
    
    # Test questions from different domains
    test_questions = [
        "How to scrape data from websites using Python?",  # Data sourcing
        "What is Docker and how to use it?",  # Development tools  
        "How does LLM extraction work?",  # LLM
        "I'm having trouble with my project submission",  # Discourse/QA
        "What visualization tools should I use?",  # Data viz
    ]
    
    print("=== Testing Unified Knowledge Base Search ===\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"{i}. Question: {question}")
        
        start_time = time.time()
        
        try:
            # Search unified knowledge base
            search_params = {
                "q": question,
                "query_by": "content",
                "per_page": 10,
                "num_typos": 2,
                "highlight_full_fields": "content",
            }
            
            results = client.collections["unified_knowledge_base"].documents.search(search_params)
            search_time = time.time() - start_time
            
            hits = results.get("hits", [])
            print(f"   Results: {len(hits)} found in {search_time:.3f}s")
            
            # Show top 3 results with relevance scores
            for j, hit in enumerate(hits[:3], 1):
                doc = hit.get("document", {})
                score = hit.get("text_match", 0)
                content_preview = doc.get("content", "")[:100] + "..."
                
                print(f"     {j}. Score: {score:,} - {content_preview}")
            
            print()
            
        except Exception as e:
            print(f"   Error: {e}")
            print()

if __name__ == "__main__":
    asyncio.run(test_unified_search())
