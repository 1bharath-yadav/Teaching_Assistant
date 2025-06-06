# ******************** spell checking utilities ********************#
"""
Spell checking and text correction utilities.
"""

import logging
import ollama
from lib import config

# ******************** configuration and logging ********************#
logger = logging.getLogger(__name__)
cfg = config.get_config()

# ******************** LLM-based correction functions ********************#


async def correct_with_llm(question: str, client=None) -> str:
    """
    LLM-based correction using Ollama with function tool calling.
    Falls back to regular prompting if function calling is not supported.
    """
    # List of models that support function calling
    function_calling_models = [
        "llama3.2:1b",
        "llama3.2:3b",
        "llama3.1:8b",
        "llama3.1:70b",
    ]

    # Try to use a model that supports function calling first
    model_to_use = cfg.ollama.default_model
    if model_to_use not in function_calling_models:
        # Check if any function-calling model is available
        available_models = cfg.ollama.models
        for func_model in function_calling_models:
            if func_model in available_models:
                model_to_use = func_model
                break

    try:
        # First, try with function calling if the model supports it
        if model_to_use in function_calling_models:
            response = ollama.chat(
                model=model_to_use,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that corrects spelling and grammar while preserving the original intent of the text.",
                    },
                    {
                        "role": "user",
                        "content": f"Please correct the spelling and grammar in this question: {question}",
                    },
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "correct_text",
                            "description": "Correct spelling and grammar in the provided text while preserving original intent",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "corrected_text": {
                                        "type": "string",
                                        "description": "The corrected version of the text with proper spelling and grammar",
                                    },
                                },
                                "required": ["corrected_text"],
                            },
                            "strict": True,
                        },
                    }
                ],
            )

            # Check if the model used a tool call
            if (
                hasattr(response, "message")
                and hasattr(response.message, "tool_calls")
                and response.message.tool_calls
            ):
                tool_call = response.message.tool_calls[0]
                if tool_call.function.name == "correct_text":
                    function_args = tool_call.function.arguments

                    # The arguments are already a dict in the new ollama library
                    corrected_text = function_args.get("corrected_text", question)

                    logger.info(
                        f"Text corrected using function tool call with model {model_to_use}"
                    )
                    return corrected_text

            # Fallback to regular response content if no tool call
            content = response.message.content if hasattr(response, "message") else ""

            # Check if the content looks like raw function call JSON
            if content and content.strip().startswith('{"type":"function"'):
                import re
                import json

                # Try to extract corrected text from JSON content
                try:
                    # Handle malformed JSON by using regex
                    match = re.search(r'"corrected_text"\s*:\s*"([^"]*)"', content)
                    if match:
                        corrected_text = match.group(1)
                        logger.info(
                            f"Extracted corrected text from JSON content with model {model_to_use}"
                        )
                        return corrected_text
                except Exception as e:
                    logger.warning(f"Failed to extract from JSON content: {e}")

            return content.strip() if content else question

    except Exception as e:
        if "does not support tools" in str(e):
            logger.info(
                f"Model {model_to_use} doesn't support function calling, falling back to regular prompting"
            )
        else:
            logger.warning(
                f"Function calling failed: {e}, falling back to regular prompting"
            )

    # Fallback: Use regular prompting without function calls
    try:
        response = ollama.chat(
            model=cfg.ollama.default_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that corrects spelling and grammar while preserving the original intent of the text. Return only the corrected text without any additional commentary.",
                },
                {
                    "role": "user",
                    "content": f"Correct the spelling and grammar in this question, return only the corrected text: {question}",
                },
            ],
        )

        content = response.message.content if hasattr(response, "message") else ""
        corrected_text = content.strip() if content else question

        logger.info(
            f"Text corrected using regular prompting with model {cfg.ollama.default_model}"
        )
        return corrected_text

    except Exception as e:
        logger.error(f"Error in LLM-based correction: {e}")
        return question


async def spell_check_and_correct(question: str, client=None) -> str:
    """
    LLM-based spell check and correction using Ollama function tool calling.
    Uses Ollama directly with function tools for better structured correction results.
    """
    # Use Ollama function tool calling for better results
    corrected = await correct_with_llm(question, client)
    return corrected
