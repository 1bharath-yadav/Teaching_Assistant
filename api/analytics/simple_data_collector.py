# ******************** RAG analytics data collector ********************#
"""
Simple data collector for RAG system analytics
Collects all prompt data and exports to readable files
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# ******************** data collection class ********************#


class SimpleDataCollector:
    def __init__(self, output_dir: str = "rag_analytics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.data = []

    def collect_prompt_data(
        self,
        user_prompt: str,
        corrected_prompt: str,
        classified_collections: List[str],
        search_results: List[Dict[str, Any]],
        context_chunks: str,
        openai_response: str,
        token_usage: Optional[Dict[str, int]] = None,
        response_time: Optional[float] = None,
        full_search_results: Optional[List[Dict[str, Any]]] = None,
    ):
        """Collect all data for a single prompt interaction"""

        # Extract complete documents info with full content
        all_documents = []
        search_data = full_search_results if full_search_results else search_results

        for i, result in enumerate(search_data):
            doc_content = result.get("document", {}).get("content", "")
            doc_info = {
                "rank": i + 1,
                "collection": result.get("collection", "unknown"),
                "hybrid_score": result.get("hybrid_score", 0),
                "search_type": result.get("search_type", "unknown"),
                "content_length": len(doc_content),
                "full_content": doc_content,  # Store complete content
                # Keep preview for backward compatibility
                "content_preview": (
                    doc_content[:200] + "..." if len(doc_content) > 200 else doc_content
                ),
            }
            all_documents.append(doc_info)

        # Collect all data
        prompt_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_prompt": user_prompt,
            "corrected_prompt": corrected_prompt,
            "classified_collections": classified_collections,
            "all_search_documents": all_documents,
            "total_search_results": len(search_data),
            "context_sent_to_openai": {
                "full_context": context_chunks,  # Complete context sent to OpenAI
                "context_length": len(context_chunks),
                "context_preview": (
                    context_chunks[:500] + "..."
                    if len(context_chunks) > 500
                    else context_chunks
                ),
            },
            "openai_response": openai_response,
            "token_usage": token_usage or {},
            "response_time_seconds": response_time,
        }

        self.data.append(prompt_data)

        # Auto-save after each collection
        self.save_to_file()

        return prompt_data

    def save_to_file(self):
        """Save collected data to JSON file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rag_data_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        # Also save a readable text summary
        self.save_readable_summary()

    def save_readable_summary(self):
        """Save a human-readable summary"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rag_summary_{timestamp}.txt"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("RAG System Analytics Summary\n")
            f.write("=" * 50 + "\n\n")

            for i, entry in enumerate(self.data, 1):
                f.write(f"QUERY #{i}\n")
                f.write(f"Timestamp: {entry['timestamp']}\n")
                f.write(f"User Prompt: {entry['user_prompt']}\n")
                f.write(f"Corrected Prompt: {entry['corrected_prompt']}\n")
                f.write(f"Collections: {', '.join(entry['classified_collections'])}\n")
                f.write(f"Total Results: {entry['total_search_results']}\n")

                context_info = entry.get("context_sent_to_openai", {})
                f.write(
                    f"Context Length: {context_info.get('context_length', 0)} chars\n"
                )

                if entry["token_usage"]:
                    f.write(f"Tokens Used: {entry['token_usage']}\n")

                if entry["response_time_seconds"]:
                    f.write(f"Response Time: {entry['response_time_seconds']:.2f}s\n")

                f.write("\nTop Documents:\n")
                docs = entry.get("all_search_documents", entry.get("top_documents", []))
                for doc in docs[:5]:  # Top 5 for summary
                    content_len = doc.get(
                        "content_length", len(doc.get("content_preview", ""))
                    )
                    f.write(
                        f"  {doc['rank']}. {doc['collection']} (score: {doc['hybrid_score']:.3f}, length: {content_len} chars)\n"
                    )

                f.write(f"\nFull Context Sent to OpenAI:\n")
                full_context = context_info.get(
                    "full_context", entry.get("context_preview", "")
                )
                f.write(
                    f"{full_context[:500]}{'...' if len(full_context) > 500 else ''}\n"
                )

                f.write(f"\nResponse Preview: {entry['openai_response'][:200]}...\n")
                f.write("\n" + "-" * 80 + "\n\n")


# Global collector instance
data_collector = SimpleDataCollector()
