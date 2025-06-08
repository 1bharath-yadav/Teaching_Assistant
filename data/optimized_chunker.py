#!/usr/bin/env python3
"""
Optimized chunking system for Teaching Assistant.
Handles both discourse posts and chapter content chunking.
"""

import datetime
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import html2text
import yaml
from dataclasses import dataclass

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not available. Using fallback token estimation.")

try:
    from bs4 import BeautifulSoup

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BEAUTIFULSOUP_AVAILABLE = False
    print("Warning: BeautifulSoup not available. Using html2text fallback.")

try:
    from readability import Document

    READABILITY_AVAILABLE = True
except ImportError:
    Document = None
    READABILITY_AVAILABLE = False
    print(
        "Warning: readability-lxml not available. Skipping content extraction optimization."
    )

try:
    from markdownify import markdownify as md

    MARKDOWNIFY_AVAILABLE = True
except ImportError:
    md = None
    MARKDOWNIFY_AVAILABLE = False
    print("Warning: markdownify not available. Using html2text fallback.")


@dataclass
class ChunkConfig:
    """Configuration for chunking process."""

    max_tokens: int = 4096
    chunk_overlap: int = 200
    min_chunk_length: int = 50
    max_chunk_length: int = 8000
    preserve_headers: bool = True
    extract_metadata: bool = True


class OptimizedChunker:
    """Optimized chunker for discourse and chapter content."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize chunker with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = True
        self.h2t.ignore_images = True

        # Initialize tiktoken encoding if available
        if TIKTOKEN_AVAILABLE and tiktoken:
            try:
                self.encoding = tiktoken.encoding_for_model("gpt-4o")
            except Exception:
                self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_path} not found. Using defaults.")
            return {}

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback estimation: ~4 characters per token
            return len(text) // 4

    def clean_html_content(self, html_content: str) -> str:
        """Convert HTML content to clean plain text with advanced noise removal."""
        if not html_content:
            return ""

        try:
            # Use readability to extract main content if available
            if READABILITY_AVAILABLE and Document:
                try:
                    doc = Document(html_content)
                    # Extract main content using readability
                    clean_html = doc.summary()

                    # Convert to markdown for better structure preservation
                    if MARKDOWNIFY_AVAILABLE and md:
                        clean_text = md(clean_html, heading_style="ATX", bullets="-")
                    else:
                        # Fallback to html2text
                        clean_text = self.h2t.handle(clean_html)

                except Exception as e:
                    print(f"Readability extraction failed, using fallback: {e}")
                    # Fallback to standard processing
                    clean_text = self._fallback_html_cleaning(html_content)
            else:
                clean_text = self._fallback_html_cleaning(html_content)

            # Apply advanced content cleaning
            clean_text = self._advanced_content_cleaning(clean_text)

            return clean_text.strip()
        except Exception as e:
            print(f"Error cleaning HTML content: {e}")
            return html_content.strip()

    def _fallback_html_cleaning(self, html_content: str) -> str:
        """Fallback HTML cleaning when advanced libraries aren't available."""
        if BEAUTIFULSOUP_AVAILABLE and BeautifulSoup:
            # Use BeautifulSoup for better HTML processing
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text with better spacing
            clean_text = soup.get_text(separator=" ", strip=True)

            # Convert to markdown-like format for better structure
            if MARKDOWNIFY_AVAILABLE and md:
                # Re-parse as HTML and convert to markdown
                clean_text = md(str(soup), heading_style="ATX", bullets="-")

            return clean_text
        else:
            # Final fallback to html2text
            return self.h2t.handle(html_content)

    def _advanced_content_cleaning(self, content: str) -> str:
        """Apply advanced content cleaning to remove noise and improve embeddings quality."""
        if not content:
            return ""

        # Remove base64 encoded images (major noise source)
        content = re.sub(
            r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", "[IMAGE_REMOVED]", content
        )

        # Remove very long base64 strings in general
        content = re.sub(
            r"[A-Za-z0-9+/=]{500,}", "[LONG_ENCODED_DATA_REMOVED]", content
        )

        # Remove JSON error responses and technical noise
        content = re.sub(
            r'\{[^}]*"error"[^}]*\}',
            "[ERROR_RESPONSE_REMOVED]",
            content,
            flags=re.IGNORECASE,
        )
        content = re.sub(
            r'\{[^}]*"id":\s*"chatcmpl-[^}]+\}', "[API_RESPONSE_REMOVED]", content
        )

        # Remove malformed JSON blocks
        content = re.sub(
            r'\{[^{}]*"[^"]*":\s*[^,}]*(?:,[^{}]*"[^"]*":\s*[^,}]*)*\}',
            "[JSON_DATA_REMOVED]",
            content,
            flags=re.MULTILINE,
        )

        # Remove excessive technical output (stack traces, long JSON responses)
        lines = content.split("\n")
        cleaned_lines = []

        in_code_block = False
        json_brace_count = 0
        consecutive_technical_lines = 0
        consecutive_empty_lines = 0

        for line in lines:
            original_line = line
            line = line.strip()

            # Track code blocks - preserve them but with limits
            if line.startswith("```"):
                in_code_block = not in_code_block
                if len(line) <= 20:  # Keep reasonable code block markers
                    cleaned_lines.append(original_line)
                continue

            # Skip excessively long lines that are likely noise
            if len(line) > 800:
                consecutive_technical_lines += 1
                if consecutive_technical_lines < 2:  # Allow some but not too many
                    cleaned_lines.append("[LONG_LINE_TRUNCATED]")
                continue
            else:
                consecutive_technical_lines = 0

            # Handle empty lines - don't allow too many consecutive
            if not line:
                consecutive_empty_lines += 1
                if consecutive_empty_lines < 3:  # Max 2 consecutive empty lines
                    cleaned_lines.append("")
                continue
            else:
                consecutive_empty_lines = 0

            # Enhanced JSON block detection
            if "{" in line or "}" in line:
                json_brace_count += line.count("{") - line.count("}")

            # If we're in a large JSON block, skip it
            if json_brace_count > 5:
                continue

            # Reset if JSON block is properly closed
            if json_brace_count <= 0:
                json_brace_count = 0

            # Remove lines that are pure technical noise
            if self._is_technical_noise_line(line):
                continue

            # Remove common web artifacts
            if self._is_web_artifact(line):
                continue

            # Keep the line if it passes all filters
            cleaned_lines.append(original_line)

        content = "\n".join(cleaned_lines)

        # Advanced text normalization
        content = self._normalize_text_content(content)

        # Enhanced link processing
        content = self._process_links_and_media(content)

        return content.strip()

    def _is_web_artifact(self, line: str) -> bool:
        """Detect common web artifacts that should be removed."""
        if not line:
            return False

        web_artifact_patterns = [
            r"^cookies?\s*[:=]",  # Cookie declarations
            r"^accept\s*[:=]",  # Accept headers
            r"^user-agent\s*[:=]",  # User agent strings
            r"^content-type\s*[:=]",  # Content type headers
            r"^<!DOCTYPE",  # HTML doctype
            r"^<html",  # HTML tags
            r"^<meta",  # Meta tags
            r"^<link",  # Link tags
            r"^<script",  # Script tags
            r"^<style",  # Style tags
            r"^\s*window\.",  # JavaScript window objects
            r"^\s*document\.",  # JavaScript document objects
            r"^=+$",  # Lines of just equal signs
            r"^-+$",  # Lines of just dashes (when too long)
            r"^\*+$",  # Lines of just asterisks
            r"^_+$",  # Lines of just underscores
        ]

        for pattern in web_artifact_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        # Check for overly repetitive characters
        unique_chars = set(line.replace(" ", ""))
        if len(unique_chars) == 1 and len(line) > 10:
            return True

        return False

    def _normalize_text_content(self, content: str) -> str:
        """Advanced text normalization for better embedding quality."""
        # Remove excessive whitespace and normalize
        content = re.sub(r"\n\s*\n\s*\n+", "\n\n", content)
        content = re.sub(r" {3,}", " ", content)  # Remove 3+ consecutive spaces
        content = re.sub(r"\t+", " ", content)  # Replace tabs with spaces

        # Fix common text artifacts
        content = re.sub(r"&nbsp;", " ", content)
        content = re.sub(r"&amp;", "&", content)
        content = re.sub(r"&lt;", "<", content)
        content = re.sub(r"&gt;", ">", content)
        content = re.sub(r"&quot;", '"', content)

        # Remove stray Unicode characters that often indicate encoding issues
        content = re.sub(r"[\ufeff\u200b\u200c\u200d]", "", content)

        return content

    def _process_links_and_media(self, content: str) -> str:
        """Enhanced link and media processing."""
        # Clean up YouTube embed patterns but preserve the meaningful part
        content = re.sub(
            r"\[!\[.*?\]\(https://i\.ytimg\.com/.*?\)\]\(https://youtu\.be/([^)]+)\)",
            r"[YouTube Video: https://youtu.be/\1]",
            content,
        )

        # Clean up image URLs that are just noise (but keep meaningful captions)
        content = re.sub(
            r"!\[\]\(https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp|svg)[^)]*\)",
            "[IMAGE]",
            content,
        )

        # Keep meaningful image references with captions
        content = re.sub(
            r"!\[([^\]]{10,})\]\(https?://[^\s]+\.(?:png|jpg|jpeg|gif|webp|svg)[^)]*\)",
            r"[Image: \1]",
            content,
        )

        # Preserve meaningful links - don't remove them, just clean up formatting
        # Only remove markdown link formatting for very short or meaningless text
        content = re.sub(
            r"\[([^\]]{1,3})\]\([^)]+\)", r"\1", content
        )  # Remove links with very short text (like [1], [2], etc.)

        # Keep longer, meaningful links intact - they're valuable for context
        return content

    def _is_technical_noise_line(self, line: str) -> bool:
        """Determine if a line is technical noise that should be removed."""
        if not line:
            return True

        # Check for various noise patterns
        noise_patterns = [
            r"^[A-Za-z0-9+/=]{50,}$",  # Long base64 strings
            r"^[\d\.\-\s]+ms\s+TTL=\d+",  # Ping output
            r"^Reply from \d+\.\d+\.\d+\.\d+:",  # Network responses
            r"^Packets: Sent = \d+,",  # Network statistics
            r"^Approximate round trip times",  # Network timing
            r'^"[a-z_]+":',  # JSON property lines
            r"^[\{\},\[\]]+$",  # Pure JSON delimiters
            r'^["\s,]+$',  # Just quotes and commas
            r"^\s*\d+\s*$",  # Just numbers
            r"^Error:|^Warning:|^Info:",  # Log prefixes
            r"^\s*at\s+.*\([^)]+:\d+:\d+\)",  # Stack trace lines
            r"^console\.",  # JavaScript console commands
            r"^function\s*\(",  # Function declarations (often noise in scraped content)
            r"^var\s+\w+\s*=",  # Variable declarations
            r"^let\s+\w+\s*=",  # Let declarations
            r"^const\s+\w+\s*=",  # Const declarations
            r"^import\s+",  # Import statements
            r"^export\s+",  # Export statements
            r"^require\s*\(",  # Require statements
            r"^\s*\/\*",  # Start of block comments
            r"^\s*\*\/",  # End of block comments
            r"^\s*\/\/",  # Line comments (when standalone)
            r"^#include\s+",  # C/C++ includes
            r"^using\s+",  # Using statements
            r"^namespace\s+",  # Namespace declarations
            r"^\s*\{[^}]*\}\s*$",  # Small JSON objects on single line
            r"^HTTP/\d\.\d\s+\d+",  # HTTP response codes
            r"^Content-Type:",  # HTTP headers
            r"^Content-Length:",  # HTTP headers
            r"^Cache-Control:",  # HTTP headers
            r"^Set-Cookie:",  # HTTP headers
            r"^Location:",  # HTTP headers
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",  # ISO timestamps (when standalone)
            r"^[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}$",  # UUIDs
            r"^[a-f0-9]{32}$",  # MD5 hashes
            r"^[a-f0-9]{40}$",  # SHA1 hashes
            r"^[a-f0-9]{64}$",  # SHA256 hashes
        ]

        for pattern in noise_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        # Check for lines that are mostly punctuation or symbols
        alphanumeric_chars = sum(1 for c in line if c.isalnum())
        if len(line) > 20 and alphanumeric_chars / len(line) < 0.3:
            return True

        # Check for extremely repetitive content
        if len(set(line.replace(" ", ""))) < 3 and len(line) > 10:
            return True

        return False

    def clean_markdown_content(self, content: str) -> str:
        """Clean markdown content while preserving valuable links and context."""
        if not content:
            return ""

        # Apply basic content cleaning first
        content = self._advanced_content_cleaning(content)

        # Additional markdown-specific cleaning
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                cleaned_lines.append("")
                continue

            # Keep headers as they provide structure
            if line.startswith("#"):
                cleaned_lines.append(line)
                continue

            # Keep bullet points and numbered lists
            if re.match(r"^[-*+]\s+", line) or re.match(r"^\d+\.\s+", line):
                cleaned_lines.append(line)
                continue

            # Keep lines with meaningful links (preserve the full markdown link)
            if "[" in line and "](" in line:
                # Check if it's a meaningful link (not just [1], [2], etc.)
                meaningful_links = re.findall(r"\[([^\]]{4,})\]\([^)]+\)", line)
                if meaningful_links:
                    cleaned_lines.append(line)  # Keep the full line with links
                    continue
                else:
                    # Remove short reference links but keep the rest of the line
                    line = re.sub(r"\[([^\]]{1,3})\]\([^)]+\)", r"\1", line)
                    if line.strip():
                        cleaned_lines.append(line)
                    continue

            # Keep code blocks and inline code
            if "`" in line:
                cleaned_lines.append(line)
                continue

            # Keep regular content lines
            cleaned_lines.append(line)

        # Rejoin and clean up excessive whitespace
        content = "\n".join(cleaned_lines)
        content = re.sub(r"\n\s*\n\s*\n+", "\n\n", content)

        return content.strip()

    def _clean_discourse_specific_content(self, content: str) -> str:
        """Clean discourse-specific content patterns and forum artifacts."""
        if not content:
            return ""

        # Remove common discourse artifacts
        discourse_patterns = [
            # Remove user mention patterns like @username
            (r"@[\w.-]+\s*", ""),
            # Remove quote blocks that are just noise
            (r"^\s*>\s*$", ""),
            # Remove discourse-specific URLs and internal links
            (r"\bhttps?://discourse\.[^\s]+", "[DISCOURSE_LINK]"),
            # Remove category breadcrumbs
            (r"^Categories?\s*[:>]\s*.*$", ""),
            # Remove post numbers and meta info
            (r"^Post\s*#?\d+\s*$", ""),
            # Remove "Reply to" patterns
            (r"^Reply to\s+@?[\w.-]+\s*$", ""),
            # Remove view count patterns
            (r"\b\d+\s*views?\b", ""),
            # Remove like count patterns
            (r"\b\d+\s*likes?\b", ""),
            # Remove "show more" type buttons
            (r"^(Show more|Load more|View more|Read more)\.?$", ""),
            # Remove discourse timestamp patterns
            (
                r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s+\d{4})?\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\b",
                "",
            ),
            # Remove "edited" notifications
            (r"^edited\s+.*$", ""),
            # Remove discourse-specific UI elements
            (r"^(Topic|Category|Tags?)\s*:", ""),
        ]

        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            original_line = line
            line_strip = line.strip()

            # Skip empty lines
            if not line_strip:
                cleaned_lines.append("")
                continue

            # Apply discourse-specific pattern removal
            should_keep = True
            for pattern, replacement in discourse_patterns:
                if re.match(pattern, line_strip, re.IGNORECASE):
                    if replacement == "":
                        should_keep = False
                        break
                    else:
                        line_strip = re.sub(
                            pattern, replacement, line_strip, flags=re.IGNORECASE
                        )

            if not should_keep:
                continue

            # Remove lines that are just discourse navigation or UI elements
            if self._is_discourse_ui_element(line_strip):
                continue

            # Keep the line if it passed all filters
            if line_strip:  # Don't add empty lines after processing
                cleaned_lines.append(line_strip)
            else:
                cleaned_lines.append("")

        # Clean up excessive whitespace
        content = "\n".join(cleaned_lines)
        content = re.sub(r"\n\s*\n\s*\n+", "\n\n", content)

        return content.strip()

    def _is_discourse_ui_element(self, line: str) -> bool:
        """Check if a line contains discourse UI elements that should be removed."""
        if not line:
            return False

        # Common discourse UI patterns
        ui_patterns = [
            r"^(Home|Latest|New|Unread|Top|Categories|Users|Search)$",
            r"^(Previous|Next|First|Last)\s*$",
            r"^\d+\s*of\s*\d+\s*$",  # Page numbers
            r"^Page\s*\d+\s*$",
            r"^Loading\.\.\.?\s*$",
            r"^(Subscribe|Unsubscribe|Bookmark|Share|Flag|Edit|Delete|Reply)$",
            r"^(Solved|Unsolved|Closed|Locked|Pinned|Unlisted)$",
            r"^\d+\s*(replies?|views?|users?|posts?)\s*$",
            r"^(Created|Updated|Last reply)\s*:?\s*$",
            r"^(Participants|Frequent Posters)\s*:?\s*$",
        ]

        for pattern in ui_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        return False

    def chunk_content(
        self, content: str, chunk_id_base: str, config: ChunkConfig
    ) -> List[Dict[str, Any]]:
        """
        Chunk content into pieces under max_tokens.

        Args:
            content: Text content to chunk
            chunk_id_base: Base ID for chunks (e.g., topic_id, file_path)
            config: Chunking configuration

        Returns:
            List of chunk dictionaries
        """
        if not content or not content.strip():
            return []

        content = content.strip()
        content_tokens = self._estimate_tokens(content)

        # If content is small enough, return as single chunk
        if content_tokens <= config.max_tokens:
            return [
                {
                    "content": content,
                    "chunk_id": str(chunk_id_base),
                    "token_count": content_tokens,
                    "chunk_index": 0,
                    "total_chunks": 1,
                }
            ]

        # Split content intelligently
        chunks = self._intelligent_split(content, config)

        # Create chunk objects
        result_chunks = []
        for i, chunk_content in enumerate(chunks):
            chunk_tokens = self._estimate_tokens(chunk_content)
            result_chunks.append(
                {
                    "content": chunk_content,
                    "chunk_id": f"{chunk_id_base}_{i+1}",
                    "token_count": chunk_tokens,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
            )

        return result_chunks

    def _intelligent_split(self, content: str, config: ChunkConfig) -> List[str]:
        """Split content intelligently preserving structure."""
        chunks = []

        # Try splitting by paragraphs first
        paragraphs = content.split("\n\n")
        current_chunk = ""
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            para_tokens = self._estimate_tokens(paragraph)

            # If paragraph itself is too long, split it further
            if para_tokens > config.max_tokens:
                # Save current chunk if it has content
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0

                # Split the long paragraph
                sub_chunks = self._split_long_paragraph(paragraph, config)
                chunks.extend(sub_chunks[:-1])  # Add all but last

                # Start new chunk with last sub-chunk
                if sub_chunks:
                    current_chunk = sub_chunks[-1]
                    current_tokens = self._estimate_tokens(current_chunk)

            elif current_tokens + para_tokens > config.max_tokens:
                # Current chunk is full, start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
                current_tokens = para_tokens
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens += para_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return [chunk for chunk in chunks if len(chunk) >= config.min_chunk_length]

    def _split_long_paragraph(self, paragraph: str, config: ChunkConfig) -> List[str]:
        """Split a long paragraph by sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            if current_tokens + sentence_tokens > config.max_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def process_discourse_posts(
        self,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> None:
        """
        Process discourse posts from scraped_posts.json following enhanced approach.

        Args:
            input_file: Path to input JSON file
            output_file: Path to output JSON file
            max_tokens: Maximum tokens per chunk
        """
        # Use config defaults if not provided
        if input_file is None:
            input_file = self.config.get("discourse", {}).get(
                "input_file", "data/discourse/scraped_posts.json"
            )
        if output_file is None:
            output_file = self.config.get("discourse", {}).get(
                "output_file", "data/discourse/discourse_chunks.json"
            )

        # Ensure we have valid paths
        if not input_file or not output_file:
            print("Error: input_file and output_file must be provided")
            return

        input_path = Path(input_file)
        if not input_path.exists():
            print(f"Input file {input_file} not found.")
            return

        print(f"Processing discourse posts from {input_file}")

        # Load scraped posts
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                scraped_posts = json.load(f)
        except Exception as e:
            print(f"Error loading posts: {e}")
            return

        # Group posts by topic_id (following enhanced approach)
        topics = {}
        for post in scraped_posts:
            topic_id = post.get("topic_id")
            if not topic_id:
                continue

            if topic_id not in topics:
                topics[topic_id] = {
                    "topic_id": topic_id,
                    "topic_title": post.get("topic_title", ""),
                    "posts": [],
                }
            topics[topic_id]["posts"].append(post)

        print(f"Found {len(topics)} unique topics with {len(scraped_posts)} posts")

        # Process topics into chunks
        chunk_config = ChunkConfig(max_tokens=max_tokens)
        output_data = []

        for topic_id, topic_data in topics.items():
            try:
                # Process single topic (following enhanced approach)
                posts = topic_data["posts"]

                # Create basic document structure
                doc = {
                    "topic_id": topic_id,
                    "topic_title": topic_data["topic_title"],
                    "url": f"https://discourse.onlinedegree.iitm.ac.in/t/{topic_id}",
                    "timestamp": posts[0].get("created_at", "") if posts else "",
                    "metadata": {
                        "post_count": len(posts),
                        "usernames": [],
                    },
                }

                # Combine all post content with proper cleaning
                all_content = []
                usernames = set()

                for post in posts:
                    content = post.get("post_content", "").strip()
                    if content:
                        all_content.append(content)

                    username = post.get("username", "").strip()
                    if username:
                        usernames.add(username)

                # Clean HTML content using advanced cleaning methods
                clean_content_parts = []
                for content in all_content:
                    if content:
                        # Use the enhanced clean_html_content method which includes:
                        # - Readability extraction for main content
                        # - Advanced noise removal (base64 images, JSON errors, etc.)
                        # - Technical artifact filtering
                        # - Proper HTML to markdown conversion
                        cleaned_content = self.clean_html_content(content)
                        if (
                            cleaned_content and len(cleaned_content.strip()) > 10
                        ):  # Skip very short content
                            clean_content_parts.append(cleaned_content)

                doc["content"] = "\n\n".join(clean_content_parts)

                # Apply additional discourse-specific cleaning
                if doc["content"]:
                    # Remove discourse-specific noise patterns
                    doc["content"] = self._clean_discourse_specific_content(
                        doc["content"]
                    )

                # Apply additional discourse-specific cleaning
                if doc["content"]:
                    # Remove discourse-specific noise patterns
                    doc["content"] = self._clean_discourse_specific_content(
                        doc["content"]
                    )

                # Update metadata
                doc["metadata"]["usernames"] = list(usernames)

                # Parse timestamp
                try:
                    timestamp = doc["timestamp"]
                    if timestamp:
                        created_at = datetime.datetime.strptime(
                            timestamp, "%Y-%m-%dT%H:%M:%S.%fZ"
                        )
                        formatted_timestamp = created_at.strftime("%Y-%m-%d")
                    else:
                        formatted_timestamp = "unknown"
                except Exception:
                    formatted_timestamp = "unknown"

                doc["timestamp"] = formatted_timestamp

                # Skip if no content
                if not doc["content"].strip():
                    continue

                # Chunk the content
                chunks = self.chunk_content(doc["content"], topic_id, chunk_config)

                # Create documents for each chunk
                for chunk in chunks:
                    chunk_doc = {
                        "id": chunk["chunk_id"],
                        "topic_id": str(topic_id),
                        "topic_title": doc["topic_title"],
                        "content": chunk["content"],
                        "url": doc["url"],
                        "timestamp": doc["timestamp"],
                        "token_count": chunk["token_count"],
                        "chunk_index": chunk["chunk_index"],
                        "total_chunks": chunk["total_chunks"],
                        "source_type": "discourse",
                        "metadata": doc["metadata"],
                    }
                    output_data.append(chunk_doc)

            except Exception as e:
                print(f"Failed to process topic {topic_id}: {e}")
                continue

        # Save output
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(output_data)} discourse chunks to {output_file}")

    def process_chapter_module(
        self, module_path: Path, module_name: str, max_tokens: int = 4096
    ) -> List[Dict[str, Any]]:
        """
        Process a single chapter module into chunks.

        Args:
            module_path: Path to module directory
            module_name: Name of the module
            max_tokens: Maximum tokens per chunk

        Returns:
            List of chunk dictionaries
        """
        chunks = []
        chunk_config = ChunkConfig(max_tokens=max_tokens)

        # Check if module directory is valid
        if not module_path.exists():
            print(f"WARNING: Module path does not exist: {module_path}")
            return chunks

        if not module_path.is_dir():
            print(f"WARNING: Module path is not a directory: {module_path}")
            return chunks

        # Find all markdown files in the module
        md_files = list(module_path.glob("**/*.md"))

        if not md_files:
            print(
                f"WARNING: No markdown files found in module {module_name} at {module_path}"
            )
            return chunks

        print(f"Found {len(md_files)} markdown files in module {module_name}")

        processed_files = 0
        failed_files = []

        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():
                    print(f"WARNING: Empty file skipped: {md_file.name}")
                    continue

                # Generate relative path for chunk ID
                rel_path = md_file.relative_to(module_path)
                chunk_id_base = f"{module_name}_{str(rel_path).replace('/', '_').replace('.md', '')}"

                # Extract metadata if enabled
                metadata = self._extract_file_metadata(md_file, content)

                # Clean markdown content while preserving links
                cleaned_content = self.clean_markdown_content(content)

                # Chunk the cleaned content
                file_chunks = self.chunk_content(
                    cleaned_content, chunk_id_base, chunk_config
                )

                if not file_chunks:
                    print(f"WARNING: No chunks generated for file: {md_file.name}")
                    failed_files.append(md_file.name)
                    continue

                # Add metadata to chunks
                for chunk in file_chunks:
                    chunk.update(
                        {
                            "module": module_name,
                            "file_path": str(rel_path),
                            "source_type": "chapter",
                            "metadata": metadata,
                        }
                    )
                    chunks.append(chunk)

                processed_files += 1
                print(f"Processed {md_file.name}: {len(file_chunks)} chunks")

            except Exception as e:
                print(f"ERROR: Failed to process {md_file}: {e}")
                failed_files.append(md_file.name)
                continue

        # Summary for this module
        print(
            f"Module {module_name} summary: {processed_files}/{len(md_files)} files processed, {len(chunks)} total chunks"
        )
        if failed_files:
            print(f"Failed files in {module_name}: {', '.join(failed_files)}")

        return chunks

    def _extract_file_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract metadata from markdown file."""
        metadata = {
            "filename": file_path.name,
            "size_bytes": len(content.encode("utf-8")),
            "line_count": len(content.split("\n")),
        }

        # Try to extract title from first heading
        lines = content.split("\n")
        for line in lines[:10]:  # Check first 10 lines
            if line.strip().startswith("# "):
                metadata["title"] = line.strip()[2:].strip()
                break

        return metadata

    def process_all_chapters(
        self, base_path: Optional[str] = None, max_tokens: int = 4096
    ) -> None:
        """
        Process all chapter modules into separate chunks.json files.

        Args:
            base_path: Base path to chapters directory
            max_tokens: Maximum tokens per chunk
        """
        # Use config default if not provided
        if base_path is None:
            base_path = self.config.get("chapters", {}).get(
                "local_path", "data/chapters/tools-in-data-science-public"
            )

        if not base_path:
            print("WARNING: No base path provided for chapters processing")
            return

        base_path_obj = Path(base_path)
        if not base_path_obj.exists():
            print(
                f"WARNING: Base path {base_path} not found. Skipping chapter processing."
            )
            return

        # Get modules from config
        modules = self.config.get("chapters", {}).get("modules", [])
        if not modules:
            # Auto-discover modules
            modules = [
                d.name
                for d in base_path_obj.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            ]

        if not modules:
            print(
                f"WARNING: No modules found in {base_path}. Skipping chapter processing."
            )
            return

        print(f"Processing {len(modules)} chapter modules from {base_path}")

        total_chunks = 0
        processed_modules = 0
        failed_modules = []

        for module_name in modules:
            module_path = base_path_obj / module_name
            if not module_path.exists():
                print(f"WARNING: Module {module_name} not found at {module_path}")
                failed_modules.append(module_name)
                continue

            print(f"Processing module: {module_name}")

            try:
                # Process module
                module_chunks = self.process_chapter_module(
                    module_path, module_name, max_tokens
                )

                if module_chunks:
                    # Save module chunks
                    output_file = module_path / "chunks.json"
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(module_chunks, f, ensure_ascii=False, indent=2)

                    print(f"Saved {len(module_chunks)} chunks to {output_file}")
                    total_chunks += len(module_chunks)
                    processed_modules += 1
                else:
                    print(f"WARNING: No chunks generated for module {module_name}")
                    failed_modules.append(module_name)

            except Exception as e:
                print(f"ERROR: Failed to process module {module_name}: {e}")
                failed_modules.append(module_name)

        # Summary report
        print(f"\n=== Chapter Processing Summary ===")
        print(f"Total modules found: {len(modules)}")
        print(f"Successfully processed: {processed_modules}")
        print(f"Failed modules: {len(failed_modules)}")
        if failed_modules:
            print(f"Failed module names: {', '.join(failed_modules)}")
        print(f"Total chunks generated: {total_chunks}")

        if processed_modules == 0:
            print("WARNING: No modules were successfully processed!")
        elif failed_modules:
            print(f"WARNING: {len(failed_modules)} modules failed processing")
        else:
            print("SUCCESS: All modules processed successfully!")
        print("=" * 40)

    def process_all(self, max_tokens: int = 4096) -> None:
        """Process both discourse posts and all chapter modules."""
        print("=== Starting comprehensive chunking process ===")

        # Process discourse posts
        print("\n1. Processing discourse posts...")
        self.process_discourse_posts(max_tokens=max_tokens)

        # Process chapter modules
        print("\n2. Processing chapter modules...")
        self.process_all_chapters(max_tokens=max_tokens)

        print("\n=== Chunking process completed ===")


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimized chunking for Teaching Assistant"
    )
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument(
        "--max-tokens", type=int, default=4096, help="Maximum tokens per chunk"
    )
    parser.add_argument(
        "--discourse-only", action="store_true", help="Process only discourse posts"
    )
    parser.add_argument(
        "--chapters-only", action="store_true", help="Process only chapters"
    )
    parser.add_argument("--input", help="Input file for discourse processing")
    parser.add_argument("--output", help="Output file for discourse processing")

    args = parser.parse_args()

    # Initialize chunker
    chunker = OptimizedChunker(args.config)

    if args.discourse_only:
        chunker.process_discourse_posts(
            input_file=args.input, output_file=args.output, max_tokens=args.max_tokens
        )
    elif args.chapters_only:
        chunker.process_all_chapters(max_tokens=args.max_tokens)
    else:
        chunker.process_all(max_tokens=args.max_tokens)


if __name__ == "__main__":
    main()
