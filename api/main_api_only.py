# ******************** FastAPI Backend - API Only Mode ********************#
"""
FastAPI backend configured for separate deployment (API-only mode).
Removes static file serving and focuses on API endpoints only.
"""

import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to Python path for proper imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# FastAPI core imports
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ******************** application imports ********************#
from .models.schemas import QuestionRequest, QuestionResponse
from .core.clients import config, openai_client, typesense_client
from .services.classification_service import classify_question
from .services.search_service import hybrid_search_across_collections
from .handlers.question_handler import handle_ask_question

# ******************** configuration and logging ********************#
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ******************** FastAPI application setup ********************#
app = FastAPI(
    title="Teaching Assistant API",
    description="API for answering student queries from TDS course",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ******************** CORS configuration for separate deployment ********************#
# Allow requests from frontend (adjust URLs as needed)
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js development
    "http://localhost:3001",  # Alternative Next.js port
    "https://your-frontend-domain.com",  # Production frontend domain
    "https://localhost:3000",  # HTTPS development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ALLOWED_ORIGINS + ["*"]
        if os.getenv("DEVELOPMENT") == "true"
        else ALLOWED_ORIGINS
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ******************** Global exception handler ********************#
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {exc}")

    # Return different error responses based on exception type
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid request data", "error": str(exc)},
        )
    elif isinstance(exc, ConnectionError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable", "error": str(exc)},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": config.hybrid_search.fallback.error_messages.get(
                    "search_error", "Internal server error"
                )
            },
        )


# ******************** API Routes ********************#


# Add explicit OPTIONS handler for the API endpoint
@app.options("/api/v1/ask")
async def options_ask():
    return {"message": "OK"}


# Main endpoint to ask questions about the TDS course
@app.post("/api/v1/ask", response_model=QuestionResponse)
async def ask_question(request: Request, payload: QuestionRequest) -> QuestionResponse:
    """Main endpoint to ask questions about the TDS course."""
    logger.info(f"API request received: {payload.question[:100]}...")
    return await handle_ask_question(request, payload, openai_client)


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with system status"""
    try:
        # Basic health checks
        status = {
            "status": "healthy",
            "service": "Teaching Assistant API",
            "version": "1.0.0",
            "mode": "api_only",
            "configuration": {
                "chat_provider": config.defaults.chat_provider,
                "embedding_provider": config.defaults.embedding_provider,
                "search_provider": config.defaults.search_provider,
                "hybrid_search_enabled": True,
                "collections_available": len(
                    config.hybrid_search.available_collections
                ),
            },
        }

        # Test Typesense client
        try:
            typesense_client.collections.retrieve()
            status["typesense_connection"] = "healthy"
        except Exception as e:
            logger.warning(f"Typesense connection issue: {e}")
            status["typesense_connection"] = "unhealthy"
            status["status"] = "degraded"

        # Test model provider connections
        try:
            if config.defaults.chat_provider == "openai":
                status["model_provider"] = "openai_ready"
            elif config.defaults.chat_provider == "ollama":
                status["model_provider"] = "ollama_ready"
            else:
                status["model_provider"] = f"{config.defaults.chat_provider}_configured"
        except Exception as e:
            logger.warning(f"Model provider issue: {e}")
            status["model_provider"] = "unavailable"
            status["status"] = "degraded"

        return status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "Teaching Assistant API",
            "error": str(e),
        }


@app.get("/collections")
async def get_collections():
    """Get available collections with descriptions"""
    # Use configured collections from config.yaml
    available_collections = config.hybrid_search.available_collections
    default_collections = config.hybrid_search.default_collections

    # Create descriptions mapping for available collections
    collection_descriptions = {
        "chapters_data_sourcing": "Data collection and acquisition methods",
        "chapters_data_preparation": "Data cleaning, preprocessing, transformation",
        "chapters_data_analysis": "Statistical analysis, modeling techniques",
        "chapters_data_visualization": "Charts, graphs, plotting libraries",
        "chapters_large_language_models": "LLMs, transformers, NLP models",
        "chapters_development_tools": "IDEs, libraries, frameworks",
        "chapters_deployment_tools": "Docker, cloud platforms, CI/CD",
        "chapters_project-1": "Building an API(RAG) that answers student questions",
        "chapters_project-2": "Build LLMs to answer graded assignment questions",
        "chapters_misc": "General course information and live recordings Q&A topics",
        "discourse_posts": "Community discussions and Q&A",
        "discourse_posts_optimized": "Community discussions and Q&A",
        "discourse_posts_enhanced": "Community discussions and Q&A with images",
        "unified_knowledge_base": "Combined knowledge from all chapters",
    }

    try:
        # Try to get actual collections from Typesense
        try:
            collections_response = typesense_client.collections.retrieve()
            actual_collections = [col["name"] for col in collections_response]
            logger.info(
                f"Retrieved {len(actual_collections)} collections from Typesense"
            )
        except Exception as e:
            logger.warning(f"Failed to retrieve collections from Typesense: {e}")
            actual_collections = []

        return {
            "collections": available_collections + default_collections,
            "descriptions": collection_descriptions,
            "actual_collections": actual_collections,
            "total": len(available_collections) + len(default_collections),
        }

    except Exception as e:
        logger.error(f"Error getting collections: {e}")
        return {
            "error": "Failed to retrieve collections",
            "collections": available_collections + default_collections,
        }


@app.post("/api/v1/debug/search")
async def debug_search(payload: QuestionRequest):
    """Debug endpoint to test hybrid search without generating final answer"""
    try:
        logger.info(f"Debug search for: {payload.question}")

        # Classify question
        classified_collections = await classify_question(payload)
        logger.info(
            f"Debug - Classified collections: {classified_collections['collections']}"
        )

        # Perform hybrid search with configured parameters
        search_results = await hybrid_search_across_collections(
            payload,
            classified_collections["collections"],
            top_k=config.hybrid_search.top_k,
            alpha=config.hybrid_search.alpha,
            query_embedding=None,
        )

        # Format results for debugging
        formatted_results = []
        for i, result in enumerate(search_results):
            content = result["document"].get("content", "")
            formatted_results.append(
                {
                    "rank": i + 1,
                    "content_preview": (
                        content[:200] + "..." if len(content) > 200 else content
                    ),
                    "content_length": len(content),
                    "collection": result["collection"],
                    "text_match": result.get("text_match", 0),
                    "vector_distance": result.get("vector_distance"),
                    "has_vector_search": result.get("vector_distance") is not None,
                }
            )

        return {
            "question": payload.question,
            "question_length": len(payload.question),
            "classified_collections": classified_collections["collections"],
            "total_results": len(search_results),
            "search_results": formatted_results,
            "search_parameters": {
                "alpha": config.hybrid_search.alpha,
                "top_k": config.hybrid_search.top_k,
                "collections_searched": len(classified_collections["collections"]),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Debug search error: {e}")
        logger.error(f"Debug search traceback: {traceback.format_exc()}")
        return {
            "error": str(e),
            "question": payload.question if payload else "No question provided",
        }


@app.get("/api/v1/config")
async def get_api_config():
    """Get current API configuration (non-sensitive data only)"""
    try:
        return {
            "hybrid_search": {
                "alpha": config.hybrid_search.alpha,
                "top_k": config.hybrid_search.top_k,
                "max_context_length": config.hybrid_search.max_context_length,
                "num_typos": config.hybrid_search.num_typos,
                "available_collections": config.hybrid_search.available_collections,
                "default_collections": config.hybrid_search.default_collections,
                "streaming_enabled": config.hybrid_search.answer_generation.enable_streaming,
                "link_extraction_enabled": config.hybrid_search.answer_generation.enable_link_extraction,
            },
            "providers": {
                "chat_provider": config.defaults.chat_provider,
                "embedding_provider": config.defaults.embedding_provider,
                "search_provider": config.defaults.search_provider,
            },
            "models": {
                "default_model": (
                    getattr(config.ollama, "default_model", "gemma3:4b")
                    if config.defaults.chat_provider == "ollama"
                    else getattr(config.openai, "default_model", "gpt-4o-mini")
                ),
            },
            "features": {
                "image_processing": True,
                "streaming_responses": config.hybrid_search.answer_generation.enable_streaming,
                "link_extraction": config.hybrid_search.answer_generation.enable_link_extraction,
            },
        }
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return {"error": "Failed to retrieve configuration"}


# ******************** Root endpoint ********************#
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Teaching Assistant API",
        "version": "1.0.0",
        "mode": "api_only",
        "docs": "/docs",
        "health": "/health",
        "main_endpoint": "/api/v1/ask",
    }


if __name__ == "__main__":
    import uvicorn

    # Check environment
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")

    logger.info(f"Starting API-only server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=os.getenv("DEVELOPMENT") == "true",
        log_level="info",
    )
