import pdfplumber


def extract_tables(pdf_path: str) -> list[dict]:
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            for table in page.extract_tables() or []:
                tables.append({"page_number": index, "rows": table})
    return tables
