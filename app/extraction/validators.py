from decimal import Decimal


def determine_review_reason(*, confidence: float, normalized_value, suggested_standard_line_item):
    if normalized_value is None:
        return "missing_field"
    if suggested_standard_line_item is None:
        return "missing_field"
    if confidence < 0.85:
        return "low_confidence"
    return None
