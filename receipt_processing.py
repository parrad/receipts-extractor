import pandas as pd
from bs4 import BeautifulSoup
from gmail_helpers import gmail_query_ids, get_email_html
from parser_hemkop import detect_receipt as hemkop_detect_receipt
from parser_spiceonwheels import detect_receipt as spiceonwheels_detect_receipt

def receipts_between(service, start, end, store):
    """Fetch and parse receipts between start and end dates, filtered by store."""
    import streamlit as st
    ids = gmail_query_ids(service, start, end, store)
    headers, all_rows = [], []
    for i, msg_id in enumerate(ids, 1):
        with st.spinner(f"Processing receipt {i}/{len(ids)}"):
            html = get_email_html(service, msg_id)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n")
            if store == "Hemköp":
                header, items = hemkop_detect_receipt(text)
                if header and items:
                    store_name = header.get("store") or "Hemköp"
                    headers.append(header)
                    for item in items:
                        row = {
                            "Date": header.get("date"),
                            "Store": store_name,
                            "Item": item["item"],
                            "Qty": item["qty"],
                            "UOM": item["uom"],
                            "Unit Price": item["unit_price"],
                            "Amount": item["amount"],
                            "Receipt Total": header.get("total"),
                        }
                        all_rows.append(row)
            elif store == "SpiceOnWheels":
                header, items = spiceonwheels_detect_receipt(text)
                if header and items:
                    store_name = header.get("store") or "SpiceOnWheels"
                    headers.append(header)
                    for item in items:
                        row = {
                            "Date": header.get("date"),
                            "Store": store_name,
                            "Item": item["item"],
                            "Qty": item["qty"],
                            "UOM": item["uom"],
                            "Unit Price": item["unit_price"],
                            "Amount": item["amount"],
                            "Receipt Total": header.get("total"),
                        }
                        all_rows.append(row)
    return pd.DataFrame(all_rows), headers