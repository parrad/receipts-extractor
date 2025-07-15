from ollama_client import OllamaClient
import json

def extract_receipt_with_llm_functioncall(email_text):
    """
    Use LLM function calling to extract receipt header and items from email text.
    Returns: (header_dict, items_list)
    """
    ollama = OllamaClient()
    # Define function schema (OpenAI style)
    functions = [
        {
            "name": "extract_receipt_info",
            "description": "Extracts receipt header and items from email text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "header": {"type": "object"},
                    "items": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["header", "items"]
            }
        }
    ]
    messages = [
        {"role": "system", "content": "You are an expert at extracting structured data from receipts."},
        {"role": "user", "content": f"Email text:\n\n{email_text.strip()}"}
    ]
    # This assumes OllamaClient supports a function_call method similar to OpenAI
    response = ollama.mcp_chat(messages, functions=functions, function_call={"name": "extract_receipt_info"})
    # Parse the function call result
    try:
        result = json.loads(response)
        header = result.get("header", {})
        items = result.get("items", [])
        return header, items
    except Exception:
        return {}, []
