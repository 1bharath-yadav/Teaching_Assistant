# ******************** classification service ********************#
"""
Question classification service for determining relevant collections.
"""

import json
import logging
import subprocess
from typing import Any, Dict, List, cast

from ..core.clients import config, openai_client
from ..core.tools import classification_function
from ..models.schemas import QuestionRequest

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)


# ******************** classification functions ********************#
async def classify_question(payload: QuestionRequest) -> Dict[str, Any]:
    """Classify question into relevant collections using text-based classification"""
    # Get the configured model for chat
    chat_model = config.defaults.chat_provider

    # Use configured tool calling model for classification
    if chat_model == "ollama":
        # Check if the configured tool calling model is available
        tool_calling_model = config.defaults.tool_calling_model
        try:
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

    # Create a mapping for backwards compatibility
    collection_mapping = {
        "data_sourcing": "chapters_data_sourcing",
        "data_preparation": "chapters_data_preparation",
        "data_analysis": "chapters_data_analysis",
        "data_visualization": "chapters_data_visualization",
        "large_language_models": "chapters_large_language_models",
        "development_tools": "chapters_development_tools",
        "deployment_tools": "chapters_deployment_tools",
        "project-1": "chapters_project-1",
        "project-2": "chapters_project-2",
        "misc": "chapters_misc",
    }

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
                        raise ValueError("Failed to parse Ollama function arguments")

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
                tools=cast(Any, [classification_function]),
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

        # If still no collections, use chapters_misc as fallback
        if not collections:
            collections = ["chapters_misc"]

        logger.info(f"Classified collections (before mapping): {collections}")

        # Map old collection names to new prefixed names if needed
        mapped_collections = []
        for col in collections:
            if col in collection_mapping:
                mapped_collections.append(collection_mapping[col])
            elif col in available_collections:
                mapped_collections.append(col)
            else:
                # If not a known collection name, skip it
                logger.warning(f"Skipping unknown collection: {col}")

        if not mapped_collections:
            mapped_collections = ["chapters_misc"]

        logger.info(f"Classified collections (after mapping): {mapped_collections}")

        return {"question": payload.question, "collections": mapped_collections}

    # This should never happen due to try/except, but just in case
    return {"question": payload.question, "collections": collections}
