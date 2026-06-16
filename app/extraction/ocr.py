def run_ocr_fallback(pdf_path: str) -> list[dict]:
    return [{"page_number": 1, "text": "", "method": "ocr", "source_path": pdf_path}]
