from decimal import Decimal

import pytest
from accounting.services import validate_structured_balance
from audit.models import AuditEvent
from tests.integration.test_accounting_validation_pipeline import create_structured_raw


@pytest.mark.django_db
def test_audit_events_include_validation_and_correction_payloads(user, settings):
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
                    "contas_origem": [
                        {"descricao": "A", "valor": 400},
                        {"descricao": "B", "valor": 300},
                    ],
                },
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 200},
            },
        },
        sha="sha-audit-correction",
    )

    validate_structured_balance(raw)

    completed = AuditEvent.objects.get(
        target_id=str(document.id), event_type="accounting.validation.completed"
    )
    correction = AuditEvent.objects.get(
        target_id=str(document.id), event_type="accounting.validation.correction_applied"
    )
    inconsistency = AuditEvent.objects.get(
        target_id=str(document.id), event_type="accounting.validation.inconsistency_detected"
    )
    assert completed.after["status"] == "inconsistent"
    assert correction.after["rule_id"] == "SUM_ACCOUNTS_001"
    assert correction.before["original_value"] == "690"
    assert correction.after["corrected_value"] == "700"
    assert inconsistency.after["rule_id"] == "BALANCE_EQUATION_001"
