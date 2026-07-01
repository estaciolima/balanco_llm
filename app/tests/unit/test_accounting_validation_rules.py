from decimal import Decimal

from accounting.rules import (
    BALANCE_EQUATION_RULE_ID,
    SUM_ACCOUNTS_RULE_ID,
    apply_sum_account_corrections,
    evaluate_balance_equation,
)


def _output(fields, document_type="balanco_patrimonial"):
    return {"metadados": {"tipo_documento": document_type}, "campos_analise": fields}


def test_balance_equation_passes_when_assets_equal_liabilities_plus_equity():
    finding = evaluate_balance_equation(
        _output(
            {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {"valor": 700},
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            }
        ),
        Decimal("0.01"),
    )

    assert finding.rule_id == BALANCE_EQUATION_RULE_ID
    assert finding.outcome == "passed"
    assert finding.difference == Decimal("0")


def test_balance_equation_fails_when_difference_is_material():
    finding = evaluate_balance_equation(
        _output(
            {
                "total_balanco": {"valor": 1000},
                "passivo_circulante": {"valor": 650},
                "exigivel_longo_prazo": {"valor": 0},
                "patrimonio_liquido": {"valor": 300},
            }
        ),
        Decimal("0.01"),
    )

    assert finding.outcome == "failed"
    assert finding.severity == "high"
    assert finding.difference == Decimal("50")


def test_balance_equation_allows_rounding_tolerance():
    finding = evaluate_balance_equation(
        _output(
            {
                "total_balanco": {"valor": "1000.00"},
                "passivo_circulante": {"valor": "699.996"},
                "exigivel_longo_prazo": {"valor": "0"},
                "patrimonio_liquido": {"valor": "300.00"},
            }
        ),
        Decimal("0.01"),
    )

    assert finding.outcome == "passed"


def test_balance_equation_is_not_assessable_when_required_fields_are_missing():
    finding = evaluate_balance_equation(
        _output({"total_balanco": {"valor": 1000}}),
        Decimal("0.01"),
    )

    assert finding.outcome == "not_assessable"
    assert "ausentes" in finding.message


def test_sum_accounts_corrects_material_difference():
    validated, findings = apply_sum_account_corrections(
        _output(
            {
                "exemplo": {
                    "valor": 90,
                    "tipo_obtencao": "soma_contas",
                    "contas_origem": [
                        {"descricao": "A", "valor": 40},
                        {"descricao": "B", "valor": 60},
                    ],
                }
            }
        ),
        Decimal("0.01"),
    )

    item = validated["campos_analise"]["exemplo"]
    assert item["valor_original"] == "90"
    assert item["valor_validado"] == "100"
    assert item["corrigido"] is True
    assert item["regra_correcao"] == SUM_ACCOUNTS_RULE_ID
    assert findings[0].outcome == "corrected"
    assert findings[0].difference == Decimal("10")


def test_sum_accounts_passes_when_values_match():
    validated, findings = apply_sum_account_corrections(
        _output(
            {
                "exemplo": {
                    "valor": 100,
                    "tipo_obtencao": "soma_contas",
                    "contas_origem": [
                        {"descricao": "A", "valor": 40},
                        {"descricao": "B", "valor": 60},
                    ],
                }
            }
        ),
        Decimal("0.01"),
    )

    assert validated["campos_analise"]["exemplo"]["corrigido"] is False
    assert findings[0].outcome == "passed"


def test_sum_accounts_is_not_assessable_without_origin_accounts():
    _, findings = apply_sum_account_corrections(
        _output({"exemplo": {"valor": 100, "tipo_obtencao": "soma_contas"}}),
        Decimal("0.01"),
    )

    assert findings[0].outcome == "not_assessable"


def test_sum_accounts_is_not_assessable_with_non_numeric_values():
    _, findings = apply_sum_account_corrections(
        _output(
            {
                "exemplo": {
                    "valor": 100,
                    "tipo_obtencao": "soma_contas",
                    "contas_origem": [{"descricao": "A", "valor": "abc"}],
                }
            }
        ),
        Decimal("0.01"),
    )

    assert findings[0].outcome == "not_assessable"


def test_sum_accounts_respects_tolerance():
    _, findings = apply_sum_account_corrections(
        _output(
            {
                "exemplo": {
                    "valor": "100.004",
                    "tipo_obtencao": "soma_contas",
                    "contas_origem": [{"descricao": "A", "valor": "100.00"}],
                }
            }
        ),
        Decimal("0.01"),
    )

    assert findings[0].outcome == "passed"
