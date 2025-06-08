# ******************** LangChain multimodal processing service ********************#
"""
Simplified image and PDF processing service using LangChain's multimodal capabilities.
This replaces the complex custom OCR and PDF processing with LangChain's built-in functionality.
"""

import base64
import hashlib
import logging
import time
from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)

# Import configuration
try:
    from ..core.clients import config

    CONFIG_AVAILABLE = True
except ImportError:
    config = None
    CONFIG_AVAILABLE = False
    logger.warning("Configuration not available, using defaults")


# ******************** simplified multimodal processor ********************#
class LangChainMultimodalProcessor:
    """Simplified image and PDF processor using LangChain's multimodal capabilities."""

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = "llama3.2:1b",
    ):
        """
        Initialize the processor with a multimodal-capable LLM.

        Args:
            model_provider: Provider name (ollama for simplicity)
            model_name: Specific model to use
        """
        self.model_provider = model_provider
        self.model_name = model_name

        # Initialize the LLM using ChatOllama for simplicity
        try:
            if CONFIG_AVAILABLE and config:
                # Use ChatOllama from the configuration
                self.llm = ChatOllama(
                    model=config.ollama.default_model,
                    base_url=config.ollama.base_url,
                    temperature=0.1,  # Low temperature for OCR tasks
                )
            else:
                # Default fallback
                self.llm = ChatOllama(
                    model="llama3.2:1b",
                    base_url="http://localhost:11434",
                    temperature=0.1,
                )

            logger.info(
                f"Initialized LangChain multimodal processor with {model_provider}:{model_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            # Set to None to indicate failure
            self.llm = None

    def _extract_text_from_response(self, response) -> str:
        """
        Extract text content from LLM response, handling both string and list formats.

        Args:
            response: LLM response object

        Returns:
            Extracted text as string
        """
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, str):
                return content.strip()
            elif isinstance(content, list):
                # Handle list of content blocks
                text_parts = []
                for item in content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                return " ".join(text_parts).strip()
        return ""

    def extract_text_from_image(self, base64_image: str) -> str:
        """
        Extract text from an image using LangChain's multimodal capabilities.

        Args:
            base64_image: Base64 encoded image data

        Returns:
            Extracted text or empty string if failed
        """
        if not self.llm:
            logger.error("LLM not initialized, cannot process image")
            return ""

        try:
            # Clean base64 data (remove data:image/... prefix if present)
            clean_base64 = base64_image.split(",")[-1]

            # Create multimodal message with proper format for Anthropic Claude
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "Please extract all visible text from this image. Return only the text content, no additional commentary or formatting.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{clean_base64}"},
                    },
                ]
            )

            # Get response from LLM
            response = self.llm.invoke([message])
            extracted_text = self._extract_text_from_response(response)

            if extracted_text:
                logger.info(f"Extracted text from image: {extracted_text[:100]}...")
                return extracted_text
            else:
                logger.info("No text found in image")
                return ""

        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            return ""

    def extract_text_from_pdf(self, base64_pdf: str) -> str:
        """
        Extract text from a PDF using LangChain's multimodal capabilities.

        Args:
            base64_pdf: Base64 encoded PDF data

        Returns:
            Extracted text or empty string if failed
        """
        if not self.llm:
            logger.error("LLM not initialized, cannot process PDF")
            return ""

        try:
            # Clean base64 data (remove data:application/pdf... prefix if present)
            clean_base64 = base64_pdf.split(",")[-1]

            # Create multimodal message
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "Please extract all text content from this PDF document. Return only the text content, preserving structure where possible.",
                    },
                    {
                        "type": "file",
                        "source_type": "base64",
                        "data": clean_base64,
                        "mime_type": "application/pdf",
                    },
                ]
            )

            # Get response from LLM
            response = self.llm.invoke([message])
            extracted_text = self._extract_text_from_response(response)

            if extracted_text:
                logger.info(f"Extracted text from PDF: {extracted_text[:100]}...")
                return extracted_text
            else:
                logger.info("No text found in PDF")
                return ""

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""

    def process_base64_file(
        self, base64_data: str, file_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Process base64 file (image or PDF) and return extracted information.

        Args:
            base64_data: Base64 encoded file data
            file_type: Type of file ("image", "pdf", or "auto" for detection)

        Returns:
            Dictionary with processing results
        """
        try:
            # Decode base64 to detect file type if auto
            if file_type == "auto":
                try:
                    file_data = base64.b64decode(base64_data.split(",")[-1])
                    if file_data.startswith(b"%PDF"):
                        file_type = "pdf"
                    else:
                        file_type = "image"
                except Exception:
                    # If detection fails, assume image
                    file_type = "image"

            # Extract text based on file type
            if file_type == "pdf":
                extracted_text = self.extract_text_from_pdf(base64_data)
                method = "langchain_pdf"
            else:
                extracted_text = self.extract_text_from_image(base64_data)
                method = "langchain_ocr"

            # Generate file info
            file_id = hashlib.md5(base64_data[:100].encode()).hexdigest()[:12]

            return {
                "file_id": file_id,
                "file_type": file_type,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "processing_method": method,
                "processing_successful": True,
                "timestamp": time.time(),
                "processor": f"langchain_{self.model_provider}",
            }

        except Exception as e:
            logger.error(f"Error processing base64 file: {e}")
            return {
                "file_id": "unknown",
                "file_type": "unknown",
                "extracted_text": "",
                "text_length": 0,
                "processing_method": "error",
                "processing_successful": False,
                "error": str(e),
                "timestamp": time.time(),
                "processor": f"langchain_{self.model_provider}",
            }

    def process_base64_image(self, base64_image: str) -> Dict[str, Any]:
        """
        Process base64 image and return extracted information.

        Args:
            base64_image: Base64 encoded image data

        Returns:
            Dictionary with processing results
        """
        try:
            extracted_text = self.extract_text_from_image(base64_image)
            image_id = hashlib.md5(base64_image[:100].encode()).hexdigest()[:12]

            return {
                "image_id": image_id,
                "extracted_text": extracted_text,
                "text_length": len(extracted_text),
                "processing_successful": True,
                "timestamp": time.time(),
                "processor": f"langchain_{self.model_provider}",
                "ocr_method": f"langchain_{self.model_provider}",
            }

        except Exception as e:
            logger.error(f"Error processing base64 image: {e}")
            return {
                "image_id": "unknown",
                "extracted_text": "",
                "text_length": 0,
                "processing_successful": False,
                "error": str(e),
                "timestamp": time.time(),
                "processor": f"langchain_{self.model_provider}",
                "ocr_method": "error",
            }

    def analyze_document_content(
        self, base64_data: str, analysis_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document content beyond just text extraction.

        Args:
            base64_data: Base64 encoded file data
            analysis_prompt: Custom prompt for analysis

        Returns:
            Dictionary with analysis results
        """
        if not self.llm:
            logger.error("LLM not initialized, cannot analyze document")
            return {"error": "LLM not available", "analysis": ""}

        try:
            # Default analysis prompt
            if not analysis_prompt:
                analysis_prompt = """
                Please analyze this document and provide:
                1. A brief summary of the content
                2. Key topics or subjects covered
                3. Any mathematical formulas, equations, or technical diagrams described
                4. The type of document (lecture notes, assignment, textbook chapter, etc.)
                5. Extracted text content
                
                Format your response as structured text.
                """

            # Detect file type
            try:
                file_data = base64.b64decode(base64_data.split(",")[-1])
                if file_data.startswith(b"%PDF"):
                    content_block = {
                        "type": "file",
                        "source_type": "base64",
                        "data": base64_data.split(",")[-1],
                        "mime_type": "application/pdf",
                    }
                else:
                    content_block = {
                        "type": "image",
                        "source_type": "base64",
                        "data": base64_data.split(",")[-1],
                        "mime_type": "image/jpeg",
                    }
            except Exception:
                # Fallback to image
                content_block = {
                    "type": "image",
                    "source_type": "base64",
                    "data": base64_data.split(",")[-1],
                    "mime_type": "image/jpeg",
                }

            # Create multimodal message
            message = HumanMessage(
                content=[{"type": "text", "text": analysis_prompt}, content_block]
            )

            # Get response from LLM
            response = self.llm.invoke([message])
            analysis = self._extract_text_from_response(response)

            return {
                "analysis": analysis,
                "processor": f"langchain_{self.model_provider}",
                "timestamp": time.time(),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Failed to analyze document: {e}")
            return {
                "analysis": "",
                "error": str(e),
                "processor": f"langchain_{self.model_provider}",
                "timestamp": time.time(),
                "success": False,
            }

    def process_with_image(self, text: str, base64_image: str) -> str:
        """
        Process text with image content using multimodal capabilities.

        Args:
            text: Text prompt or question
            base64_image: Base64 encoded image data

        Returns:
            Generated response as string
        """
        if not self.llm:
            logger.error("LLM not initialized, cannot process multimodal request")
            return ""

        try:
            # Clean base64 data (remove data:image/... prefix if present)
            clean_base64 = base64_image.split(",")[-1]

            # Create multimodal message with proper format for Anthropic Claude
            message = HumanMessage(
                content=[
                    {"type": "text", "text": text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{clean_base64}"},
                    },
                ]
            )

            # Get response from LLM
            response = self.llm.invoke([message])
            result = self._extract_text_from_response(response)

            logger.info(f"Generated multimodal response: {result[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Failed to process multimodal request: {e}")
            return ""

    def process_text_only(self, text: str) -> str:
        """
        Process text-only request.

        Args:
            text: Text prompt or question

        Returns:
            Generated response as string
        """
        if not self.llm:
            logger.error("LLM not initialized, cannot process text request")
            return ""

        try:
            # Create text-only message
            message = HumanMessage(content=text)

            # Get response from LLM
            response = self.llm.invoke([message])
            result = self._extract_text_from_response(response)

            logger.info(f"Generated text response: {result[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Failed to process text request: {e}")
            return ""


# ******************** global processor instance ********************#
# Initialize global processor with default settings
try:
    # Try to use Anthropic Claude if available
    multimodal_processor = LangChainMultimodalProcessor(
        model_provider="anthropic", model_name="claude-3-5-sonnet-latest"
    )
except Exception as e:
    logger.warning(f"Failed to initialize Anthropic processor: {e}")
    try:
        # Fallback to OpenAI if available
        multimodal_processor = LangChainMultimodalProcessor(
            model_provider="openai", model_name="gpt-4o"
        )
    except Exception as e2:
        logger.error(f"Failed to initialize any multimodal processor: {e2}")
        multimodal_processor = None


# ******************** backward compatibility functions ********************#
def process_image_with_ocr(base64_image: str) -> str:
    """Backward compatible function for image text extraction."""
    if not multimodal_processor:
        logger.error("Multimodal processor not available")
        return ""

    return multimodal_processor.extract_text_from_image(base64_image)


def process_file_with_text_extraction(base64_data: str) -> str:
    """Backward compatible function for file text extraction."""
    if not multimodal_processor:
        logger.error("Multimodal processor not available")
        return ""

    result = multimodal_processor.process_base64_file(base64_data, file_type="auto")
    return result.get("extracted_text", "")


def process_image_with_metadata(base64_image: str) -> Dict[str, Any]:
    """Backward compatible function for image processing with metadata."""
    if not multimodal_processor:
        logger.error("Multimodal processor not available")
        return {
            "image_id": "error",
            "extracted_text": "",
            "text_length": 0,
            "processing_successful": False,
            "error": "Multimodal processor not available",
            "timestamp": time.time(),
            "ocr_method": "error",
        }

    return multimodal_processor.process_base64_image(base64_image)


# ******************** exports ********************#
__all__ = [
    "LangChainMultimodalProcessor",
    "multimodal_processor",
    "process_image_with_ocr",
    "process_file_with_text_extraction",
    "process_image_with_metadata",
]
