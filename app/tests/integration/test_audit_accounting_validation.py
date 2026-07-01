from decimal import Decimal

import pytest
from accounting.services import validate_structured_balance
from django.urls import reverse
from tests.integration.test_accounting_validation_pipeline import create_structured_raw


@pytest.mark.django_db
def test_audit_page_displays_accounting_validation_payload(client, user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    document, raw = create_structured_raw(
        user,
        {
            "metadados": {"tipo_documento": "balanco_patrimonial"},
            "campos_analise": {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {
                    "valor": 690,
                    "tipo_obtencao": "soma_contas",
                    "contas_origem": [{"descricao": "A", "valor": 700}],
                },
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            },
        },
        sha="sha-audit-page",
    )
    validate_structured_balance(raw)
    client.force_login(user)

    response = client.get(
        reverse("audit-event-list"),
        {
            "target_type": "BalanceDocument",
            "target_id": str(document.id),
            "event_type": "accounting.validation",
        },
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "accounting.validation.correction_applied" in content
    assert "SUM_ACCOUNTS_001" in content
    assert "Original:" in content
