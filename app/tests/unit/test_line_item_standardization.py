import pytest

from standardization.models import LineItemAlias, StandardLineItem
from standardization.services import match_standard_line_item


@pytest.mark.django_db
def test_match_standard_line_item_prefers_alias():
    line_item = StandardLineItem.objects.create(
        code="cash_and_equivalents",
        display_name="Cash and Equivalents",
        category=StandardLineItem.Category.ASSET,
    )
    LineItemAlias.objects.create(
        standard_line_item=line_item,
        alias_text="Disponibilidades",
        language="pt",
    )

    matched, confidence = match_standard_line_item("Disponibilidades")

    assert matched == line_item
    assert confidence == 0.95


@pytest.mark.django_db
def test_match_standard_line_item_uses_source_account_pattern():
    line_item = StandardLineItem.objects.create(
        code="cash_and_equivalents",
        display_name="Caixa + Aplicacoes",
        category=StandardLineItem.Category.ASSET,
        source_account_patterns=["1.1.01*"],
    )

    matched, confidence = match_standard_line_item(
        "FUNDO FIXO",
        source_account_code="1.1.01.01.11010",
    )

    assert matched == line_item
    assert confidence == 0.96
