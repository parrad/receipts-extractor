import datetime as dt
import pandas as pd
import streamlit as st

from gmail_auth import get_gmail_service
from gmail_helpers import gmail_query_ids, get_email_html
from agentic_receipt_parser import OllamaClient

st.set_page_config(
    page_title="Agentic Grocery Receipt Extractor", page_icon="🤖", layout="centered"
)

st.title("🤖 Agentic Grocery Receipt Extractor (LLM)")
st.caption("LLM-based email parser for receipts - custom prompt, any store, any date (LLM extracts all)")

prompt = st.text_area(
    "Enter your LLM prompt for extraction",
    value="""Extract the receipt header and item details from the following email text. Return a JSON object with two keys: 'header' (a dict with store, date, total, etc.) and 'items' (a list of dicts with item, qty, uom, unit_price, amount, etc.).\n\nEmail text:\n\n{{email_text}}\n\nReturn only the JSON object.""",
    height=200,
)

st.info("All available receipts will be processed. The LLM will extract store and date from the email text itself.")

if st.button("Fetch & Extract Receipts with LLM"):
    gmail_service = get_gmail_service()
    # Fetch all receipts from a very broad date range (e.g., last 5 years)
    today = dt.date.today()
    ids = gmail_query_ids(gmail_service, today - dt.timedelta(days=5*365), today)
    ollama = OllamaClient()
    all_rows = []
    headers = []
    for i, msg_id in enumerate(ids, 1):
        with st.spinner(f"Processing receipt {i}/{len(ids)}"):
            html = get_email_html(gmail_service, msg_id)
            email_text = pd.read_html(html)[0].to_string() if '<table' in html else html
            # Replace placeholder in prompt
            user_prompt = prompt.replace("{{email_text}}", email_text.strip())
            system = "You are an expert at extracting structured data from receipts."
            try:
                response = ollama.generate(user_prompt, system=system)
                import json
                data = json.loads(response)
                header = data.get("header", {})
                items = data.get("items", [])
                # Only proceed if both store and date are present in header
                if not header.get("store") or not header.get("date"):
                    st.info(f"Skipping a receipt: LLM could not extract store and date.")
                    continue
                headers.append(header)
                for item in items:
                    row = {"Date": header.get("date"), "Store": header.get("store"), "Item": item.get("item"), "Qty": item.get("qty"), "UOM": item.get("uom"), "Unit Price": item.get("unit_price"), "Amount": item.get("amount"), "Receipt Total": header.get("total")}
                    all_rows.append(row)
            except Exception as e:
                st.warning(f"Failed to parse a receipt: {e}")
    df = pd.DataFrame(all_rows)
    if df.empty:
        st.info("No receipts found or extracted.")
    else:
        st.success(f"Parsed {len(headers)} receipt(s)")
        st.dataframe(df, use_container_width=True)
        buffer = pd.ExcelWriter("receipts_llm.xlsx", engine="openpyxl")
        df.to_excel(buffer, index=False, sheet_name="Receipts")
        buffer.close()
        with open("receipts_llm.xlsx", "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                file_name="receipts_llm.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
