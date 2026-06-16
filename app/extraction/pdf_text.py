import fitz


def detect_has_text(pdf_path: str) -> bool:
    with fitz.open(pdf_path) as document:
        return any(page.get_text("text").strip() for page in document)


def extract_native_text(pdf_path: str) -> list[dict]:
    rows = []
    with fitz.open(pdf_path) as document:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                rows.append({"page_number": index, "text": text, "method": "native_text"})
    return rows
