from pydantic import BaseModel
from typing import List, Optional

class ReceiptItem(BaseModel):
    item: str
    qty: str
    uom: Optional[str] = None
    unit_price: Optional[str] = None
    amount: Optional[str] = None

class ReceiptHeader(BaseModel):
    store: Optional[str] = None
    date: Optional[str] = None
    total: Optional[str] = None
    items_count: Optional[str] = None
    # Add more fields as needed

class ReceiptExtraction(BaseModel):
    header: ReceiptHeader
    items: List[ReceiptItem]
