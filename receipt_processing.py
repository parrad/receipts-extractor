import pandas as pd
from bs4 import BeautifulSoup
from gmail_helpers import gmail_query_ids, get_email_html
from parser_hemkop import detect_and_parse
from parser_spiceonwheels import parse_spiceonwheels_receipt

def receipts_between(service, start, end, selected_store="All"):
    """Fetch and parse receipts between start and end dates, filtered by store."""
    import streamlit as st
    ids = gmail_query_ids(service, start, end)
    headers, all_rows = [], []
    for i, msg_id in enumerate(ids, 1):
        with st.spinner(f"Processing receipt {i}/{len(ids)}"):
            html = get_email_html(service, msg_id)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n")
            # Try Hemköp parser first
            header, items = detect_and_parse(text)
            if header and items:
                store_name = header.get("store") or "Hemköp"
                if selected_store in ("All", "Hemköp"):
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
            else:
                # Try SpiceOnWheels parser
                df, hdrs = parse_spiceonwheels_receipt(text)
                if not df.empty:
                    store_name = "SpiceOnWheels"
                    if selected_store in ("All", "SpiceOnWheels"):
                        headers.append(hdrs)
                        for _, row in df.iterrows():
                            all_rows.append({
                                "Date": hdrs.get("date"),
                                "Store": store_name,
                                "Item": row["Product"],
                                "Qty": row["Quantity"],
                                "UOM": "",  # UOM not available in SpiceOnWheels parser
                                "Unit Price": row["Price"] / row["Quantity"] if row["Quantity"] > 0 else 0,
                                "Amount": row["Price"],
                                "Receipt Total": hdrs.get("total"),
                            })
    return pd.DataFrame(all_rows), headers