"""
Streamlit web app that connects to the user's Gmail, finds grocery
receipts within a user-selected date range, parses them with rule-based
logic (currently Hemköp-style layout), and lets the user download the
results as an Excel file.
"""

from __future__ import annotations
import base64
import datetime as dt
import os
import pickle
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# -------------------- Gmail Auth --------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = Path("token.pkl")
CLIENT_SECRET = Path(os.getenv("GMAIL_CLIENT_SECRET", "client_secret.json"))


def get_gmail_service():
    """Return an authenticated Gmail service (pickle token cache)."""
    creds = None
    if TOKEN_FILE.exists():
        creds = pickle.loads(TOKEN_FILE.read_bytes())
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                st.error(
                    "client_secret.json not found. Upload it or set GMAIL_CLIENT_SECRET path environment variable."
                )
                st.stop()
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_bytes(pickle.dumps(creds))
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# -------------------- Gmail Helpers --------------------


def gmail_query_ids(service, start: dt.date, end: dt.date) -> List[str]:
    """Return message-IDs for receipts between start and end (inclusive)."""
    # Gmail expects dates in YYYY/MM/DD format
    start_str = start.strftime("%Y/%m/%d")
    end_str = (end + dt.timedelta(days=1)).strftime("%Y/%m/%d")
    query = (
        f"after:{start_str} before:{end_str} "
        f"(subject:(Här kommer ditt digitala kvitto) OR from:(hemkop@kund.hemkop.se))"
    )
    results = service.users().messages().list(userId="me", q=query).execute()
    return [m["id"] for m in results.get("messages", [])]


def get_email_html(service, msg_id: str) -> str:
    """Return HTML body of email."""
    msg = (
        service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )
    payload = msg.get("payload", {})
    # Case 1: multipart
    parts = payload.get("parts", [])
    for p in parts:
        if p.get("mimeType") == "text/html" and "data" in p.get("body", {}):
            data = p["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    # Case 2: single-part
    if payload.get("mimeType") == "text/html" and "data" in payload.get("body", {}):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""


# -------------------- Parser – Hemköp --------------------


def normalize(txt: str) -> str:
    """Normalize text to NFKC form and replace non-breaking spaces."""
    return unicodedata.normalize("NFKC", txt).replace("\xa0", " ")


def parse_hemkop(text: str) -> Tuple[Dict, List[Dict]]:
    """Parse Hemköp receipt text into structured header and items."""
    lines = [line.strip() for line in normalize(text).splitlines() if line.strip()]
    header: Dict = {"store": None, "date": None, "total": None, "items_count": None}
    items: List[Dict] = []
    parsing_items = True

    for idx, line in enumerate(lines):
        low = line.lower()

        # store
        if not header["store"] and "hemköp" in low:
            header["store"] = line
        # date (allow time after date)
        if not header["date"]:
            m = re.search(r"\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?", line)
            if m:
                header["date"] = m.group()
        # total SEK (allow extra spaces)
        if not header["total"] and "totalt" in low and "sek" in low:
            m = re.search(r"totalt\s+([\d,.]+)\s*sek", low)
            if not m:
                m = re.search(r"([\d,.]+)\s*SEK", line, re.IGNORECASE)
            if m:
                header["total"] = m.group(1)
        # items count
        if not header["items_count"]:
            m = re.search(r"totalt\s+(\d+)\s+varor", low)
            if m:
                header["items_count"] = m.group(1)

        # Stop parsing items at summary/payment lines
        if low.startswith("totalt") or low.startswith("mottaget"):
            parsing_items = False

        # Parse items only before summary/payment lines
        if parsing_items:
            # 1. Weight-based item (previous line is name)
            m = re.search(r"([\d,.]+)kg\*(\d+,\d{2})kr/kg\s+([\d,]+)", line)
            if m and idx > 0:
                qty, unit_p, total = m.groups()
                items.append(
                    {
                        "item": lines[idx - 1],
                        "qty": qty,
                        "uom": "KG",
                        "unit_price": unit_p,
                        "amount": total,
                    }
                )
                continue  # skip further processing for this line

            # 2. Multi-quantity item: e.g. "MARIEKEX 200G         2st*10,95      21,90"
            m = re.search(r"(.+?)\s+(\d+)([a-zA-Z]+)\*(\d+,\d{2})\s+([\d,]+)$", line)
            if m:
                name, qty, uom, unit_price, amount = m.groups()
                items.append(
                    {
                        "item": name.strip(),
                        "qty": qty,
                        "uom": uom.upper(),
                        "unit_price": unit_price,
                        "amount": amount,
                    }
                )
                continue

            # 3. Simple line item PRICE at end (including discounts)
            if re.match(r".+\s+-?\d{1,3},\d{2}$", line):
                parts = re.split(r"\s{2,}", line)
                if len(parts) >= 2:
                    name, price = parts[0], parts[-1]
                else:
                    price = re.search(r"-?[\d,]+$", line).group()
                    name = line[: line.rfind(price)].strip()
                items.append(
                    {
                        "item": name,
                        "qty": "1",
                        "uom": "ST",
                        "unit_price": price,
                        "amount": price,
                    }
                )
                continue

    return header, items


def detect_and_parse(text: str):
    """Detect store type and parse receipt text accordingly."""
    if "hemköp" in text.lower():
        return parse_hemkop(text)
    # placeholder for future stores
    return None, []


# -------------------- Receipt Processing --------------------


def receipts_between(service, start: dt.date, end: dt.date):
    """Fetch and parse receipts between start and end dates."""
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


# -------------------- Streamlit UI --------------------
st.set_page_config(
    page_title="Grocery Receipt Extractor", page_icon="🧾", layout="centered"
)

st.title("🧾 Swedish Grocery Receipt Extractor")
st.caption("Rule-based email parser (Hemköp) - data download as Excel")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", dt.date.today() - dt.timedelta(days=7))
with col2:
    end_date = st.date_input("End date", dt.date.today())

if start_date > end_date:
    st.error("Start date must be on or before end date.")
    st.stop()

if st.button("Fetch receipts"):
    gmail_service = get_gmail_service()
    df, hdrs = receipts_between(gmail_service, start_date, end_date)
    if df.empty:
        st.info("No receipts found in the given date range.")
    else:
        st.success(f"Parsed {len(hdrs)} receipt(s)")
        st.dataframe(df, use_container_width=True)
        # Excel download
        buffer = pd.ExcelWriter("receipts.xlsx", engine="openpyxl")
        df.to_excel(buffer, index=False, sheet_name="Receipts")
        buffer.close()
        with open("receipts.xlsx", "rb") as f:
            st.download_button(
                "Download Excel",
                f,
                file_name="receipts.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
