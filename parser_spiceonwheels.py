import re
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd

import re
from typing import Dict, List, Tuple

def parse_receipt(text: str) -> Tuple[Dict, List[Dict]]:
    """Parse SpiceOnWheels receipt text into structured header and items."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    hdrs = {}
    items = []
    order_match = re.search(r'\[Order #(\d+)\] \(([^)]+)\)', text)
    if order_match:
        hdrs['store'] = 'SpiceOnWheels'
        # Format date to YYYY-MM-DD
        try:
            parsed_date = datetime.strptime(order_match.group(2), "%B %d, %Y")
            hdrs['date'] = parsed_date.strftime("%Y-%m-%d")
        except Exception:
            hdrs['date'] = order_match.group(2)
        hdrs['order'] = order_match.group(1)

    # Extract total
    for i, line in enumerate(lines):
        if line.lower().startswith('total:'):
            if i + 1 < len(lines):
                total_match = re.match(r'([\d,.]+)', lines[i + 1])
                if total_match:
                    hdrs['total'] = float(total_match.group(1).replace(',', '.'))
            break

    # Find indices for items section
    try:
        start_idx = lines.index("Product")
    except ValueError:
        start_idx = 0
    try:
        subtotal_idx = next(i for i, l in enumerate(lines) if l.lower().startswith('subtotal'))
    except StopIteration:
        subtotal_idx = len(lines)

    i = start_idx + 3  # Skip headers
    while i < subtotal_idx - 3:
        product = lines[i]
        # Find quantity
        if i + 1 < subtotal_idx and re.match(r'^\d+$', lines[i + 1]):
            qty = int(lines[i + 1])
            # Find price (number followed by 'kr')
            if i + 3 < subtotal_idx and re.match(r'^[\d,.]+$', lines[i + 2]) and lines[i + 3].lower() == 'kr':
                price_val = float(lines[i + 2].replace(',', '.'))
                items.append({
                    'item': product,
                    'qty': qty,
                    'uom': 'ST',
                    'unit_price': price_val / qty if qty > 0 else 0,
                    'amount': price_val
                })
                i += 4  # Move to next item block
            else:
                i += 1
        else:
            i += 1

    return hdrs, items

def detect_receipt(text: str):
    """Detects if the receipt is from SpiceOnWheels."""
    if "spiceonwheels" in text.lower():
        return parse_receipt(text)
    return {}, []
