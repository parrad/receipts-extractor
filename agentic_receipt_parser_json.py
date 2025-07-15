from ollama_client import OllamaClient
import json

def extract_receipt_with_llm_json(email_text, prompt_template=None):
    """
    Use LLM to extract receipt header and items from email text using prompt+JSON parsing.
    Returns: (header_dict, items_list)
    """
    ollama = OllamaClient()
    if prompt_template is None:
        prompt_template = (
            "Extract the receipt header and item details from the following email text. "
            "Return a JSON object with two keys: 'header' (a dict with store, date, total, etc.) "
            "and 'items' (a list of dicts with item, qty, uom, unit_price, amount, etc.).\n\n"
            "Email text:\n\n{email_text}\n\nReturn only the JSON object."
        )
    prompt = prompt_template.format(email_text=email_text.strip())
    system = "You are an expert at extracting structured data from receipts."
    response = ollama.generate(prompt, system=system)
    try:
        data = json.loads(response)
        header = data.get("header", {})
        items = data.get("items", [])
        return header, items
    except Exception:
        return {}, []
