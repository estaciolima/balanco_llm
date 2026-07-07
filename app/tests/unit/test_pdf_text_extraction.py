from unittest.mock import MagicMock, patch

from extraction.pdf_text import detect_has_text, extract_native_text


@patch("extraction.pdf_text.fitz.open")
def test_detect_has_text_returns_true_when_any_page_has_text(mock_open):
    page_empty = MagicMock()
    page_empty.get_text.return_value = ""
    page_text = MagicMock()
    page_text.get_text.return_value = "Cash 1000"
    document = MagicMock()
    document.__enter__.return_value = [page_empty, page_text]
    mock_open.return_value = document

    assert detect_has_text("sample.pdf") is True


@patch("extraction.pdf_text.fitz.open")
def test_extract_native_text_collects_non_empty_pages(mock_open):
    page = MagicMock()
    page.get_text.return_value = "Cash 1000"
    document = MagicMock()
    document.__enter__.return_value = [page]
    mock_open.return_value = document

    rows = extract_native_text("sample.pdf")

    assert rows == [{"page_number": 1, "text": "Cash 1000", "method": "native_text"}]
