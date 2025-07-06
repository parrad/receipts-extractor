import datetime as dt
import pandas as pd
import streamlit as st

from gmail_auth import get_gmail_service
from receipt_processing import receipts_between

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