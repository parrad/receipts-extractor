import unicodedata

def normalize(txt: str) -> str:
    """Normalize text to NFKC form and replace non-breaking spaces."""
    return unicodedata.normalize("NFKC", txt).replace("\xa0", " ")