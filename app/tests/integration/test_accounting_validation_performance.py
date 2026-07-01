from decimal import Decimal

import pytest
from accounting.services import validate_structured_balance
from tests.integration.test_accounting_validation_pipeline import create_structured_raw


@pytest.mark.django_db
def test_validation_of_30_fields_completes_under_three_seconds(user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    fields = {
        f"campo_{index}": {
            "valor": index,
            "tipo_obtencao": "soma_contas",
            "contas_origem": [{"descricao": "Conta", "valor": index}],
        }
        for index in range(30)
    }
    fields.update(
        {
            "total_balanco": {"valor": 1000},
            "passivo_circulante": {"valor": 700},
            "exigivel_longo_prazo": {"valor": 0},
            "patrimonio_liquido": {"valor": 300},
        }
    )
    _, raw = create_structured_raw(
        user,
        {"metadados": {"tipo_documento": "balanco_patrimonial"}, "campos_analise": fields},
        sha="sha-performance",
    )

    run = validate_structured_balance(raw)

    assert run.duration_ms < 3000
