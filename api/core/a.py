# ******************** data processing pielline ********************#
import json
import logging
import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
import base64
import io
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the lib directory to Python path
curr_dir = Path(__file__).parent
lib_path = curr_dir / ".." / ".." / "lib"
sys.path.insert(0, str(lib_path))

# Add the data directory to Python path for image processor
data_path = curr_dir / ".." / ".." / "data"
sys.path.insert(0, str(data_path))

# Import from centralized configuration system
from lib.embeddings import generate_embedding
from lib.config import get_config, get_openai_client, get_typesense_client

# Enhanced image processing with EasyOCR support
try:
    import easyocr

    EASYOCR_AVAILABLE = True
    logger.info("EasyOCR library is available")
except ImportError:
    easyocr = None
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR library not available - using basic fallback")


# Image processor class for OCR functionality
class EnhancedImageProcessor:
    def __init__(self, use_ocr=True, ocr_languages=None):
        self.use_ocr = use_ocr and EASYOCR_AVAILABLE
        self.ocr_languages = ocr_languages or ["en"]

        if self.use_ocr and easyocr is not None:
            try:
                self.ocr_reader = easyocr.Reader(self.ocr_languages)
                logger.info(f"EasyOCR initialized with languages: {self.ocr_languages}")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.use_ocr = False

    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """Extract text from image using EasyOCR or fallback"""
        if not self.use_ocr:
            logger.warning("OCR not available - cannot extract text from image")
            return ""

        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Check if image is valid and not too small/large
            width, height = image.size
            if width < 50 or height < 50:
                logger.debug(f"Image too small for OCR: {width}x{height}")
                return ""
            if width > 2000 or height > 2000:
                logger.debug(f"Image too large for OCR: {width}x{height}")
                return ""

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Convert PIL Image to numpy array for EasyOCR
            import numpy as np

            image_array = np.array(image)

            # Use OCR to extract text
            results = self.ocr_reader.readtext(image_array)

            # Extract text from results
            extracted_text = []
            for bbox, text, confidence in results:
                # Check if confidence is above threshold
                try:
                    conf_score = (
                        float(confidence)
                        if isinstance(confidence, (int, float, str))
                        else 0.0
                    )
                    if conf_score > 0.5:  # Only include high-confidence text
                        extracted_text.append(text.strip())
                except (ValueError, TypeError):
                    continue

            result_text = " ".join(extracted_text)
            if result_text:
                logger.info(f"Extracted text from image: {result_text[:100]}...")
            return result_text

        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            return ""

    def process_base64_image(self, base64_image: str) -> Dict[str, Any]:
        """Process base64 image and return extracted information"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image.split(",")[-1])

            # Extract text using OCR
            extracted_text = self.extract_text_from_image(image_data)

            # Generate image info
            image_id = hashlib.md5(base64_image[:100].encode()).hexdigest()[:12]

            return {
                "image_id": image_id,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "ocr_enabled": self.use_ocr,
                "processing_successful": True,
            }

        except Exception as e:
            logger.error(f"Error processing base64 image: {e}")
            return {
                "image_id": "unknown",
                "extracted_text": "",
                "text_length": 0,
                "ocr_enabled": self.use_ocr,
                "processing_successful": False,
                "error": str(e),
            }


# Initialize clients using centralized config
config = get_config()
openai_client = get_openai_client()
typesense_client = get_typesense_client()

# Initialize global image processor
image_processor = EnhancedImageProcessor(use_ocr=True, ocr_languages=["en"])


# Request payload structure
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # base64-encoded


class LinkObject(BaseModel):
    url: str
    text: str


class QuestionResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None  # Keep for backward compatibility
    links: Optional[List[LinkObject]] = None  # New field for structured links


# Function definition for OpenAI function calling (updated format)
classification_function = {
    "type": "function",
    "function": {
        "name": "classify_question",
        "description": "Classify a student's query into one or more relevant TDS course collections.",
        "parameters": {
            "type": "object",
            "properties": {
                "collections": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": config.hybrid_search.available_collections,
                    },
                }
            },
            "required": ["collections"],
            "additionalProperties": False,
        },
    },
    "strict": True,  # Ensure strict validation of function parameters
}


async def classify_question(payload: QuestionRequest) -> Dict[str, Any]:
    """Classify question into relevant collections using text-based classification"""
    # Get the configured model for chat
    chat_model = config.defaults.chat_provider

    # Use configured tool calling model for classification
    if chat_model == "ollama":
        # Check if the configured tool calling model is available
        tool_calling_model = config.defaults.tool_calling_model
        try:
            import subprocess

            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if tool_calling_model in result.stdout:
                model_name = tool_calling_model
                logger.info(
                    f"Using {tool_calling_model} for question classification (tool calling)"
                )
            else:
                model_name = config.ollama.default_model
                logger.info(
                    f"{tool_calling_model} not available, using {model_name} for classification"
                )
        except Exception as e:
            logger.warning(f"Could not check available models: {e}")
            model_name = config.ollama.default_model
    elif chat_model == "openai":
        model_name = config.openai.default_model
    elif chat_model == "azure":
        model_name = config.azure.deployment_name or config.openai.default_model
    else:
        model_name = (
            config.defaults.tool_calling_model
        )  # fallback to configured tool calling model

    # Available collections for classification
    available_collections = config.hybrid_search.available_collections
    collections_str = ", ".join(available_collections)

    # Enhanced prompt for text-based classification
    classification_prompt = f"""
{config.hybrid_search.prompts.classification_system}

Available collections:
{collections_str}

Student Question: {payload.question}


Collections:"""

    try:
        # Try Ollama tool calling first (if using ollama and the model supports it)
        if chat_model == "ollama" and "llama3.2" in model_name:
            try:
                import ollama

                # Define tool for Ollama
                ollama_tool = {
                    "type": "function",
                    "function": {
                        "name": "classify_question",
                        "description": "Classify question into relevant course collections",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "collections": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": available_collections,
                                    },
                                    "description": "List of relevant collections for the question",
                                },
                            },
                            "required": ["collections"],
                        },
                    },
                }

                response = ollama.chat(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": config.hybrid_search.prompts.classification_system,
                        },
                        {
                            "role": "user",
                            "content": payload.question,
                        },
                    ],
                    tools=[ollama_tool],
                )

                # Parse Ollama tool call response
                if response.get("message", {}).get("tool_calls"):
                    tool_call = response["message"]["tool_calls"][0]
                    function_args = tool_call["function"]["arguments"]

                    # Handle both dict and string responses
                    if isinstance(function_args, str):
                        try:
                            function_args = json.loads(function_args)
                        except json.JSONDecodeError:
                            raise ValueError(
                                "Failed to parse Ollama function arguments"
                            )

                    collections = function_args.get("collections", [])

                    # Ensure collections is a list, not a string
                    if isinstance(collections, str):
                        try:
                            collections = json.loads(collections)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, treat as single collection
                            collections = (
                                [collections]
                                if collections in available_collections
                                else []
                            )

                    logger.info(f"Ollama tool calling successful: {collections}")
                else:
                    raise ValueError("No tool calls found in Ollama response")

            except Exception as e:
                logger.warning(
                    f"Ollama tool calling failed: {e}, falling back to OpenAI client"
                )
                # Fall back to OpenAI-compatible client
                raise ValueError("Ollama tool calling failed")

        # Try structured output for OpenAI
        elif chat_model == "openai":
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": config.hybrid_search.prompts.classification_system,
                    },
                    {"role": "user", "content": payload.question},
                ],
                tools=[classification_function],
                tool_choice={
                    "type": "function",
                    "function": {"name": "classify_question"},
                },
            )

            # Parse function call result
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                function_args = tool_call.function.arguments
                args = json.loads(function_args)
                collections = args.get("collections", [])
            else:
                raise ValueError("No tool calls found")

        else:
            # Fall back to text-based classification
            raise ValueError("Using text-based classification fallback")

    except Exception as e:
        logger.info(f"Tool calling failed ({e}), using text-based classification")

        # Use text-based classification for all other cases
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": classification_prompt}],
            temperature=0.1,  # Low temperature for consistent classification
            max_tokens=100,  # Short response expected
        )

        # Parse text response
        response_content = response.choices[0].message.content
        response_text = response_content.strip() if response_content else ""
        logger.info(f"Classification response: {response_text}")

        # Extract collections from response
        collections = []
        response_lower = response_text.lower()

        # Check each available collection
        for col in available_collections:
            if col.lower() in response_lower:
                collections.append(col)

        # If no collections found, try parsing comma-separated values
        if not collections:
            potential_collections = [c.strip() for c in response_text.split(",")]
            for col in potential_collections:
                if col in available_collections:
                    collections.append(col)

        # If still no collections, use misc as fallback
        if not collections:
            collections = ["misc"]

        logger.info(f"Classified collections: {collections}")

    except Exception as e:
        # Fallback if classification fails - use default collections only
        logger.warning(f"Classification failed: {e}, using default collections.")
        collections = config.hybrid_search.default_collections

    return {"question": payload.question, "collections": collections}


async def hybrid_search_across_collections(
    payload: QuestionRequest,
    collections: List[str],
    alpha: Optional[float] = None,
    top_k: Optional[int] = None,
    query_embedding: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    """
    Simplified hybrid search using official Typesense API parameters.
    Uses configuration from config.yaml for default values.
    """
    # Use config defaults if not provided
    if alpha is None:
        alpha = config.hybrid_search.alpha
    if top_k is None:
        top_k = config.hybrid_search.top_k

    try:
        # Generate query embedding if not provided
        if query_embedding is None:
            query_embedding = generate_embedding(payload.question)

        # Prepare searches for multi-search
        searches = []
        for collection in collections:
            search_params = {
                "collection": collection,
                "q": payload.question,
                "query_by": "content",
                "per_page": top_k,
                "num_typos": config.hybrid_search.num_typos,
            }

            # Add hybrid search if embeddings are available
            if query_embedding and alpha > 0:
                search_params["vector_query"] = (
                    f"embedding:([{','.join(map(str, query_embedding))}], alpha:{alpha})"
                )
                logger.info(f"Hybrid search in '{collection}' with alpha={alpha}")
            else:
                logger.info(f"Keyword search in '{collection}'")

            searches.append(search_params)

        # Execute multi-search
        multi_results = typesense_client.multi_search.perform({"searches": searches})

        # Collect all hits with minimal processing
        all_hits = []
        for i, collection in enumerate(collections):
            if i >= len(multi_results["results"]):
                continue

            results = multi_results["results"][i]
            hits = results.get("hits", [])

            for hit in hits:
                document = hit.get("document", {})
                if document and document.get("content", "").strip():
                    all_hits.append(
                        {
                            "document": document,
                            "collection": collection,
                            "text_match": hit.get("text_match", 0),
                            "vector_distance": hit.get("vector_distance"),
                        }
                    )

        # Return results sorted by Typesense's native scoring
        return all_hits[:top_k]

    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


async def hybrid_search_and_generate_answer(
    payload: QuestionRequest,
    collections: List[str],
    alpha: Optional[float] = None,
    top_k: Optional[int] = None,
    max_context_length: Optional[int] = None,
) -> str:
    """
    Simplified hybrid search and streaming response generation.
    Uses configuration from config.yaml for default values.
    """
    # Use config defaults if not provided
    if alpha is None:
        alpha = config.hybrid_search.alpha
    if top_k is None:
        top_k = config.hybrid_search.top_k
    if max_context_length is None:
        max_context_length = config.hybrid_search.max_context_length

    # Get the configured model for chat
    chat_model = config.defaults.chat_provider
    if chat_model == "ollama":
        model_name = config.ollama.default_model
    elif chat_model == "openai":
        model_name = config.openai.default_model
    elif chat_model == "azure":
        model_name = config.azure.deployment_name or config.openai.default_model
    else:
        model_name = "gemma3:4b"  # fallback

    user_query = payload.question

    try:
        # Step 1: Simple hybrid search using official API
        top_documents = await hybrid_search_across_collections(
            payload, collections, alpha=alpha, top_k=top_k
        )

        # Step 2: Simple context preparation
        context_parts = []
        total_length = 0
        seen_content = set()

        for i, doc_hit in enumerate(top_documents):
            doc = doc_hit["document"]
            content = doc.get("content", "").strip()

            if not content or content in seen_content:
                continue

            seen_content.add(content)
            context_part = f"--- Source {i+1} ---\n{content}\n\n"

            if total_length + len(context_part) > max_context_length:
                break

            context_parts.append(context_part)
            total_length += len(context_part)

        context_chunks = "".join(context_parts)

        # Step 3: Generate streaming response
        try:
            system_prompt = config.hybrid_search.prompts.assistant_system

            # First, generate the answer with streaming
            answer_response = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Student Query: {user_query}\n\nCourse Content:\n{context_chunks}",
                    },
                ],
                stream=True,
                temperature=(
                    config.openai.temperature
                    if chat_model == "openai"
                    else config.ollama.temperature
                ),
            )

            # Collect streaming response
            answer_parts = []
            for chunk in answer_response:
                if chunk.choices[0].delta.content:
                    answer_parts.append(chunk.choices[0].delta.content)

            answer_text = "".join(answer_parts)

            # Generate links separately for structured output
            links_response = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": config.hybrid_search.prompts.link_extraction_system,
                    },
                    {
                        "role": "user",
                        "content": f"Extract links from this content:\n{context_chunks}",
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "links_response",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "links": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string"},
                                            "text": {"type": "string"},
                                        },
                                        "required": ["url", "text"],
                                        "additionalProperties": False,
                                    },
                                },
                            },
                            "required": ["links"],
                            "additionalProperties": False,
                        },
                        "strict": True,
                    },
                },
            )

            links_content = links_response.choices[0].message.content
            try:
                links_data = (
                    json.loads(links_content) if links_content else {"links": []}
                )
                links = links_data.get("links", [])
            except:
                links = []

            # Combine answer and links
            final_response = {"answer": answer_text, "links": links}

            return json.dumps(final_response)

        except Exception as openai_error:
            logger.error(f"OpenAI API error: {openai_error}")
            return json.dumps(
                {
                    "answer": config.hybrid_search.fallback.error_messages.get(
                        "generation_error",
                        f"I found {len(context_parts)} relevant sources but encountered an issue generating the response. Please try again.",
                    ),
                    "links": [],
                }
            )

    except Exception as e:
        logger.error(f"Error in hybrid_search_and_generate_answer: {e}")
        return json.dumps(
            {
                "answer": config.hybrid_search.fallback.error_messages.get(
                    "search_error",
                    "I encountered an error while processing your question. Please try again.",
                ),
                "links": [],
            }
        )


# Enhanced image processing function with EasyOCR
def process_image_with_ocr(base64_image: str) -> str:
    """Process base64 image and extract text using EasyOCR"""
    try:
        # Use the global image processor
        result = image_processor.process_base64_image(base64_image)

        if result["processing_successful"]:
            extracted_text = result["extracted_text"]
            if extracted_text:
                logger.info(
                    f"Successfully extracted text from image: {extracted_text[:100]}..."
                )
                return extracted_text
            else:
                logger.info("No text found in image")
                return ""
        else:
            logger.error(
                f"Image processing failed: {result.get('error', 'Unknown error')}"
            )
            return ""

    except Exception as e:
        logger.error(f"Error processing image with OCR: {e}")
        return ""


# Additional function for processing multiple images or complex image data
def process_image_with_metadata(base64_image: str) -> Dict[str, Any]:
    """Process base64 image and return detailed metadata along with extracted text"""
    try:
        result = image_processor.process_base64_image(base64_image)

        # Enhance with additional metadata
        result.update(
            {
                "timestamp": time.time(),
                "ocr_method": "easyocr" if EASYOCR_AVAILABLE else "fallback",
                "languages_supported": (
                    image_processor.ocr_languages if image_processor.use_ocr else []
                ),
            }
        )

        return result

    except Exception as e:
        logger.error(f"Error processing image with metadata: {e}")
        return {
            "image_id": "error",
            "extracted_text": "",
            "text_length": 0,
            "ocr_enabled": False,
            "processing_successful": False,
            "error": str(e),
            "timestamp": time.time(),
            "ocr_method": "error",
        }
