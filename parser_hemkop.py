import re
from typing import Dict, List, Tuple
from utils import normalize

def parse_receipt(text: str) -> Tuple[Dict, List[Dict]]:
    """Parse Hemköp receipt text into structured header and items."""
    lines = [line.strip() for line in normalize(text).splitlines() if line.strip()]
    header: Dict = {"store": None, "date": None, "total": None, "items_count": None}
    items: List[Dict] = []
    parsing_items = True

    for idx, line in enumerate(lines):
        low = line.lower()

        if not header["store"] and "hemköp" in low:
            header["store"] = line

        if not header["date"]:
            m = re.search(r"\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?", line)
            if m:
                header["date"] = m.group()

        if not header["total"] and "totalt" in low and "sek" in low:
            m = re.search(r"totalt\s+([\d,.]+)\s*sek", low)
            if not m:
                m = re.search(r"([\d,.]+)\s*SEK", line, re.IGNORECASE)
            if m:
                header["total"] = m.group(1)

        if not header["items_count"]:
            m = re.search(r"totalt\s+(\d+)\s+varor", low)
            if m:
                header["items_count"] = m.group(1)

        if low.startswith("totalt") or low.startswith("mottaget"):
            parsing_items = False

        if not parsing_items:
            continue

        m = re.search(r"([\d,.]+)kg\*(\d+,\d{2})kr/kg\s+([\d,]+)", line)
        if m and idx > 0:
            qty, unit_p, total = m.groups()
            items.append({
                "item": lines[idx - 1],
                "qty": qty,
                "uom": "KG",
                "unit_price": unit_p,
                "amount": total,
            })
            continue

        m = re.search(r"(.+?)\s+(\d+)([a-zA-Z]+)\*(\d+,\d{2})\s+([\d,]+)$", line)
        if m:
            name, qty, uom, unit_price, amount = m.groups()
            items.append({
                "item": name.strip(),
                "qty": qty,
                "uom": uom.upper(),
                "unit_price": unit_price,
                "amount": amount,
            })
            continue

        if re.match(r".+\s+-?\d{1,3},\d{2}$", line):
            parts = re.split(r"\s{2,}", line)
            if len(parts) >= 2:
                name, price = parts[0], parts[-1]
            else:
                price = re.search(r"-?[\d,]+$", line).group()
                name = line[: line.rfind(price)].strip()
            items.append({
                "item": name,
                "qty": "1",
                "uom": "ST",
                "unit_price": price,
                "amount": price,
            })

    return header, items

def detect_receipt(text: str):
    """Detects if the receipt is from Hemköp."""
    if "hemköp" in text.lower():
        return parse_receipt(text)
    return None, []