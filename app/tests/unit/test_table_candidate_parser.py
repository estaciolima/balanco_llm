from decimal import Decimal

from extraction.parsers import parse_candidate_lines


def test_parse_candidate_lines_extracts_label_and_value():
    rows = [{"page_number": 1, "text": "Cash and Equivalents 1.234,56", "method": "native_text"}]

    candidates = parse_candidate_lines(rows)

    assert len(candidates) == 1
    assert candidates[0]["source_label"] == "Cash and Equivalents"
    assert candidates[0]["normalized_value"] == Decimal("1234.56")


def test_parse_candidate_lines_preserves_account_hierarchy_and_nature():
    rows = [
        {
            "page_number": 1,
            "text": "1.1.01 CAIXA E EQUIVALENTE DE CAIXA 7.138.045,42D",
            "method": "native_text",
        }
    ]

    candidates = parse_candidate_lines(rows)

    assert len(candidates) == 1
    assert candidates[0]["source_account_code"] == "1.1.01"
    assert candidates[0]["source_parent_account_code"] == "1.1"
    assert candidates[0]["source_hierarchy_level"] == 3
    assert candidates[0]["source_balance_nature"] == "D"
    assert candidates[0]["source_label"] == "CAIXA E EQUIVALENTE DE CAIXA"
    assert candidates[0]["normalized_value"] == Decimal("7138045.42")
