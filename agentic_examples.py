# Prompt template and few-shot examples for LLM-based receipt extraction

RECEIPT_EXTRACTION_PROMPT = '''
Extract the receipt header and item details from the following email text. Return a JSON object with two keys: "header" (a dict with store, date, total, etc.) and "items" (a list of dicts with item, qty, uom, unit_price, amount, etc.).

Store hint: {store_hint}

Examples:
{examples}

Email text:
"""
{email_text}
"""

Return only the JSON object.
'''

FEW_SHOT_EXAMPLES = '''
Example 1:
Email text:
"""
Hemköp
2024-05-01 12:34:56
Totalt 123,45 SEK
Totalt 5 varor
Banan 1,2kg*19,90kr/kg 23,88
Mjölk 1ST 15,00 15,00
"""
JSON:
{"header": {"store": "Hemköp", "date": "2024-05-01 12:34:56", "total": "123,45", "items_count": "5"}, "items": [{"item": "Banan", "qty": "1,2", "uom": "KG", "unit_price": "19,90", "amount": "23,88"}, {"item": "Mjölk", "qty": "1", "uom": "ST", "unit_price": "15,00", "amount": "15,00"}]}

Example 2:
Email text:
"""
[Order #1234] (2024-05-02)
Product	Quantity	Price
Paneer	2	60kr
Masala	1	40kr
Subtotal: 100kr
Pay with SWISH / CASH upon delivery.
"""
JSON:
{"header": {"store": "SpiceOnWheels", "date": "2024-05-02", "order": "1234", "total": "100"}, "items": [{"item": "Paneer", "qty": "2", "uom": "", "unit_price": "30", "amount": "60"}, {"item": "Masala", "qty": "1", "uom": "", "unit_price": "40", "amount": "40"}]}
'''
