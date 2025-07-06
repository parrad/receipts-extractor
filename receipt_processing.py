import pandas as pd
from bs4 import BeautifulSoup
from gmail_helpers import gmail_query_ids, get_email_html
from parser_hemkop import detect_and_parse

def receipts_between(service, start, end):
    """Fetch and parse receipts between start and end dates."""
    import streamlit as st
    ids = gmail_query_ids(service, start, end)
    headers, all_rows = [], []
    for i, msg_id in enumerate(ids, 1):
        with st.spinner(f"Processing receipt {i}/{len(ids)}"):
            html = get_email_html(service, msg_id)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n")
            header, items = detect_and_parse(text)
            if header and items:
                headers.append(header)
                for item in items:
                    row = {
                        "Date": header.get("date"),
                        "Store": header.get("store"),
                        "Item": item["item"],
                        "Qty": item["qty"],
                        "UOM": item["uom"],
                        "Unit Price": item["unit_price"],
                        "Amount": item["amount"],
                        "Receipt Total": header.get("total"),
                    }
                    all_rows.append(row)
    return pd.DataFrame(all_rows), headers