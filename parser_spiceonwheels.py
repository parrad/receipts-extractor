import re
import pandas as pd

def parse_spiceonwheels_receipt(body):
    # Check for a unique identifier for SpiceOnWheels
    if '[Order #' not in body or 'Pay with SWISH / CASH upon delivery.' not in body:
        return pd.DataFrame(), {}
    lines = body.splitlines()
    try:
        start_idx = lines.index('Product\tQuantity\tPrice') + 1
    except ValueError:
        return pd.DataFrame(), {}
    for i, line in enumerate(lines[start_idx:], start=start_idx):
        if line.startswith('Subtotal:'):
            end_idx = i
            break
    else:
        end_idx = len(lines)
    items = []
    for line in lines[start_idx:end_idx]:
        parts = line.split('\t')
        if len(parts) == 3:
            product, qty, price = parts
            price = float(price.replace('kr', '').replace(',', '.').strip())
            items.append({'Product': product.strip(), 'Quantity': int(qty.strip()), 'Price': price})
    df = pd.DataFrame(items)
    order_match = re.search(r'\[Order #(\d+)\] \(([^)]+)\)', body)
    hdrs = {}
    if order_match:
        hdrs['Order'] = order_match.group(1)
        hdrs['Date'] = order_match.group(2)
    return df, hdrs
