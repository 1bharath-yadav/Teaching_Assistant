#!/usr/bin/env python3
"""
Debug script to understand the function calling response format
"""
import asyncio
import ollama
import json


async def debug_function_call():
    test_question = "How can I conect to the databse?"

    try:
        response = ollama.chat(
            model="llama3.2:1b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that corrects spelling and grammar while preserving the original intent of the text.",
                },
                {
                    "role": "user",
                    "content": f"Please correct the spelling and grammar in this question: {test_question}",
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

        print("=== FULL RESPONSE ===")
        print(f"Response type: {type(response)}")
        print(
            f"Response dict: {dict(response) if hasattr(response, '__dict__') else 'No __dict__'}"
        )

        # Try to access response as dict
        if hasattr(response, "model_dump"):
            response_dict = response.model_dump()
            print(json.dumps(response_dict, indent=2))
        else:
            print("Response attributes:")
            for attr in dir(response):
                if not attr.startswith("_"):
                    try:
                        value = getattr(response, attr)
                        if not callable(value):
                            print(f"  {attr}: {value}")
                    except:
                        print(f"  {attr}: <cannot access>")

        print("\n=== MESSAGE ===")
        message = (
            response.get("message", {})
            if hasattr(response, "get")
            else getattr(response, "message", {})
        )
        print(f"Message type: {type(message)}")
        if hasattr(message, "model_dump"):
            print(json.dumps(message.model_dump(), indent=2))
        else:
            print(f"Message: {message}")

        print("\n=== TOOL CALLS ===")
        tool_calls = (
            message.get("tool_calls", [])
            if hasattr(message, "get")
            else getattr(message, "tool_calls", [])
        )
        print(f"Tool calls: {tool_calls}")

        if tool_calls:
            print("\n=== FIRST TOOL CALL ===")
            tool_call = tool_calls[0]
            print(f"Tool call: {tool_call}")

            print("\n=== FUNCTION ARGUMENTS ===")
            function_args = (
                tool_call["function"]["arguments"]
                if hasattr(tool_call, "__getitem__")
                else getattr(tool_call.function, "arguments", None)
            )
            print(f"Type: {type(function_args)}")
            print(f"Value: {function_args}")

            if isinstance(function_args, str):
                try:
                    parsed_args = json.loads(function_args)
                    print(f"Parsed: {parsed_args}")
                    print(
                        f"Corrected text: {parsed_args.get('corrected_text', 'NOT FOUND')}"
                    )
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
            elif isinstance(function_args, dict):
                print(
                    f"Corrected text: {function_args.get('corrected_text', 'NOT FOUND')}"
                )

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_function_call())
