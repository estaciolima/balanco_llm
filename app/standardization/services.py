from fnmatch import fnmatchcase
import unicodedata

from standardization.models import LineItemAlias, StandardLineItem


def normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(ascii_value.casefold().split())


def match_standard_line_item(source_label: str, source_account_code: str = ""):
    if source_account_code:
        for line_item in StandardLineItem.objects.filter(is_active=True):
            if any(fnmatchcase(source_account_code, pattern) for pattern in line_item.source_account_patterns):
                return line_item, 0.96

    alias = (
        LineItemAlias.objects.select_related("standard_line_item")
        .filter(alias_text__iexact=source_label)
        .first()
    )
    if alias:
        return alias.standard_line_item, 0.95

    line_item = StandardLineItem.objects.filter(display_name__iexact=source_label).first()
    if line_item:
        return line_item, 0.9

    normalized_source = normalize_label(source_label)
    for alias in LineItemAlias.objects.select_related("standard_line_item").filter(
        standard_line_item__is_active=True
    ):
        if normalize_label(alias.alias_text) == normalized_source:
            return alias.standard_line_item, 0.93

    for line_item in StandardLineItem.objects.filter(is_active=True):
        if normalize_label(line_item.display_name) == normalized_source:
            return line_item, 0.88

    return None, 0.3
