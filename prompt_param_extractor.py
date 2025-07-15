from ollama_client import OllamaClient
import json
from typing import Optional, Tuple

def extract_store_and_dates_from_prompt(user_prompt: str) -> Optional[Tuple[str, str, str]]:
    """
    Use LLM to extract store name and date range from the user's prompt.
    Returns (store, start_date, end_date) as strings, or None if extraction fails.
    """
    ollama = OllamaClient()
    extraction_prompt = (
        "Extract the store name, start date, and end date from the following instruction. "
        "Return a JSON object with keys: 'store', 'start_date', 'end_date'. "
        "If any value is missing, set it to null.\n\n"
        "Instruction:\n{user_prompt}\n\nReturn only the JSON object."
    )
    prompt = extraction_prompt.format(user_prompt=user_prompt.strip())
    system = "You are an expert at understanding user instructions for receipt extraction."
    response = ollama.generate(prompt, system=system)
    try:
        data = json.loads(response)
        store = data.get("store")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if store and start_date and end_date:
            return store, start_date, end_date
        return None
    except Exception:
        return None
