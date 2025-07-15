import base64
import datetime as dt

def gmail_query_ids(service, start: dt.date, end: dt.date, store):
    """Return message-IDs for receipts between start and end (inclusive)."""
    start_str = start.strftime("%Y/%m/%d")
    end_str = (end + dt.timedelta(days=1)).strftime("%Y/%m/%d")
    if store == "Hemköp":
        query = (
            f"after:{start_str} before:{end_str} "
            f"(subject:(Här kommer ditt digitala kvitto) AND from:(hemkop@kund.hemkop.se))"
        )
    elif store == "SpiceOnWheels":
        query = (
            f"after:{start_str} before:{end_str} "
            f"(subject:(Your order has been received!) AND from:(infomalmo@spiceonwheels.se))"
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