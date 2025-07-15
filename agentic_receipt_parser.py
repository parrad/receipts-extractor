from ollama_client import OllamaClient
from agentic_examples import RECEIPT_EXTRACTION_PROMPT, FEW_SHOT_EXAMPLES
import json

ollama = OllamaClient()

def extract_receipt_with_llm(email_text, store_hint=None):
    """
    Use LLM to extract receipt header and items from email text.
    Returns: (header_dict, items_list)
    """
    prompt = RECEIPT_EXTRACTION_PROMPT.format(
        store_hint=store_hint or "",
        examples=FEW_SHOT_EXAMPLES,
        email_text=email_text.strip()
    )
    system = "You are an expert at extracting structured data from receipts."
    response = ollama.generate(prompt, system=system)
    try:
        data = json.loads(response)
        header = data.get("header", {})
        items = data.get("items", [])
        return header, items
    except Exception:
        return {}, []
