from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

SUM_ACCOUNTS_RULE_ID = "SUM_ACCOUNTS_001"
BALANCE_EQUATION_RULE_ID = "BALANCE_EQUATION_001"
SUPPORTED_BALANCE_DOCUMENT_TYPES = {"balanco_patrimonial", "balanço_patrimonial"}


@dataclass(frozen=True)
class RuleFinding:
    rule_id: str
    field_path: str
    severity: str
    outcome: str
    message: str
    original_value: Decimal | None = None
    calculated_value: Decimal | None = None
    difference: Decimal | None = None
    inputs: dict[str, Any] | None = None


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def decimal_to_json(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def abs_difference(left: Decimal, right: Decimal) -> Decimal:
    return abs(left - right)


def field_value(fields: dict[str, Any], field_name: str) -> Decimal | None:
    item = fields.get(field_name)
    if not isinstance(item, dict):
        return None
    return decimal_or_none(item.get("valor_validado", item.get("valor")))


def _serialize_accounts(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    serialized = []
    for account in accounts:
        serialized.append(
            {
                "codigo": account.get("codigo"),
                "descricao": account.get("descricao"),
                "valor": decimal_to_json(decimal_or_none(account.get("valor"))),
                "natureza": account.get("natureza"),
                "grupo_original": account.get("grupo_original"),
            }
        )
    return serialized


def apply_sum_account_corrections(
    llm_output: dict[str, Any], tolerance_amount: Decimal
) -> tuple[dict[str, Any], list[RuleFinding]]:
    validated_output = deepcopy(llm_output)
    fields = validated_output.get("campos_analise", {})
    if not isinstance(fields, dict):
        return validated_output, []

    findings: list[RuleFinding] = []
    for field_name, item in fields.items():
        if not isinstance(item, dict) or item.get("tipo_obtencao") != "soma_contas":
            continue

        field_path = f"campos_analise.{field_name}.valor"
        accounts = item.get("contas_origem")
        original_value = decimal_or_none(item.get("valor"))
        if not isinstance(accounts, list) or not accounts:
            findings.append(
                RuleFinding(
                    rule_id=SUM_ACCOUNTS_RULE_ID,
                    field_path=field_path,
                    severity="warning",
                    outcome="not_assessable",
                    message="Não foi possível recalcular a soma: contas de origem ausentes.",
                    original_value=original_value,
                    inputs={"tipo_obtencao": item.get("tipo_obtencao")},
                )
            )
            continue

        account_values = [decimal_or_none(account.get("valor")) for account in accounts]
        if any(value is None for value in account_values) or original_value is None:
            findings.append(
                RuleFinding(
                    rule_id=SUM_ACCOUNTS_RULE_ID,
                    field_path=field_path,
                    severity="warning",
                    outcome="not_assessable",
                    message="Não foi possível recalcular a soma: há valor não numérico.",
                    original_value=original_value,
                    inputs={
                        "tipo_obtencao": item.get("tipo_obtencao"),
                        "contas_origem": _serialize_accounts(accounts),
                    },
                )
            )
            continue

        calculated_value = sum(account_values, Decimal("0"))
        difference = calculated_value - original_value
        inputs = {
            "tipo_obtencao": item.get("tipo_obtencao"),
            "contas_origem": _serialize_accounts(accounts),
        }
        if abs(difference) <= tolerance_amount:
            item["valor_validado"] = decimal_to_json(original_value)
            item["corrigido"] = False
            findings.append(
                RuleFinding(
                    rule_id=SUM_ACCOUNTS_RULE_ID,
                    field_path=field_path,
                    severity="info",
                    outcome="passed",
                    message="O valor corresponde à soma das contas de origem.",
                    original_value=original_value,
                    calculated_value=calculated_value,
                    difference=difference,
                    inputs=inputs,
                )
            )
            continue

        item["valor_original"] = decimal_to_json(original_value)
        item["valor_validado"] = decimal_to_json(calculated_value)
        item["corrigido"] = True
        item["regra_correcao"] = SUM_ACCOUNTS_RULE_ID
        item["diferenca_validacao"] = decimal_to_json(difference)
        findings.append(
            RuleFinding(
                rule_id=SUM_ACCOUNTS_RULE_ID,
                field_path=field_path,
                severity="warning",
                outcome="corrected",
                message="O valor extraído não corresponde à soma das contas de origem.",
                original_value=original_value,
                calculated_value=calculated_value,
                difference=difference,
                inputs=inputs,
            )
        )
    return validated_output, findings


def _assets_value(fields: dict[str, Any]) -> tuple[Decimal | None, dict[str, str]]:
    for name in ("total_ativo", "total_balanco"):
        value = field_value(fields, name)
        if value is not None:
            return value, {name: decimal_to_json(value) or ""}

    components = ("ativo_circulante", "realizavel_longo_prazo", "permanente")
    values = {name: field_value(fields, name) for name in components}
    if all(value is not None for value in values.values()):
        total = sum(values.values(), Decimal("0"))  # type: ignore[arg-type]
        return total, {name: decimal_to_json(value) or "" for name, value in values.items()}
    return None, {
        name: decimal_to_json(value) or ""
        for name, value in values.items()
        if value is not None
    }


def _liabilities_value(fields: dict[str, Any]) -> tuple[Decimal | None, dict[str, str]]:
    for name in ("total_passivo", "passivo_total"):
        value = field_value(fields, name)
        if value is not None:
            return value, {name: decimal_to_json(value) or ""}

    components = ("passivo_circulante", "exigivel_longo_prazo")
    values = {name: field_value(fields, name) for name in components}
    if all(value is not None for value in values.values()):
        total = sum(values.values(), Decimal("0"))  # type: ignore[arg-type]
        return total, {name: decimal_to_json(value) or "" for name, value in values.items()}
    return None, {
        name: decimal_to_json(value) or ""
        for name, value in values.items()
        if value is not None
    }


def evaluate_balance_equation(
    validated_output: dict[str, Any], tolerance_amount: Decimal
) -> RuleFinding:
    fields = validated_output.get("campos_analise", {})
    if not isinstance(fields, dict):
        return RuleFinding(
            rule_id=BALANCE_EQUATION_RULE_ID,
            field_path="campos_analise",
            severity="warning",
            outcome="not_assessable",
            message="Não foi possível avaliar o balanço: campos de análise ausentes.",
            inputs={},
        )

    assets, asset_inputs = _assets_value(fields)
    liabilities, liability_inputs = _liabilities_value(fields)
    equity = field_value(fields, "patrimonio_liquido")
    inputs = {
        "ativos": asset_inputs,
        "passivos": liability_inputs,
        "patrimonio_liquido": decimal_to_json(equity),
    }
    if assets is None or liabilities is None or equity is None:
        return RuleFinding(
            rule_id=BALANCE_EQUATION_RULE_ID,
            field_path="campos_analise",
            severity="warning",
            outcome="not_assessable",
            message=(
                "Não foi possível avaliar ativos - passivos - patrimônio líquido: "
                "há campos obrigatórios ausentes."
            ),
            inputs=inputs,
        )

    calculated = assets - liabilities - equity
    if abs(calculated) <= tolerance_amount:
        return RuleFinding(
            rule_id=BALANCE_EQUATION_RULE_ID,
            field_path="campos_analise",
            severity="info",
            outcome="passed",
            message="A identidade contábil ativos - passivos - patrimônio líquido está coerente.",
            original_value=Decimal("0"),
            calculated_value=calculated,
            difference=abs(calculated),
            inputs=inputs,
        )

    return RuleFinding(
        rule_id=BALANCE_EQUATION_RULE_ID,
        field_path="campos_analise",
        severity="high",
        outcome="failed",
        message=(
            "A identidade contábil ativos - passivos - patrimônio líquido "
            "apresenta diferença material."
        ),
        original_value=Decimal("0"),
        calculated_value=calculated,
        difference=abs(calculated),
        inputs=inputs,
    )
