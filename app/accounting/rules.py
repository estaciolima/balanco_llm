from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from unicodedata import normalize

SUM_ACCOUNTS_RULE_ID = "SUM_ACCOUNTS_001"
BALANCE_EQUATION_RULE_ID = "BALANCE_EQUATION_001"
EXPECTED_GROUPS_BY_FIELD = {
    "realizavel_longo_prazo": ("ativo nao circulante", "realizavel longo prazo"),
    "contas_receber_clientes_longo_prazo": (
        "ativo nao circulante",
        "realizavel longo prazo",
    ),
    "estoques_longo_prazo": ("ativo nao circulante", "realizavel longo prazo"),
    "contas_receber_empresas_ligadas_socios": (
        "ativo nao circulante",
        "realizavel longo prazo",
    ),
    "impostos_recuperar_diferidos_ativo": (
        "ativo nao circulante",
        "realizavel longo prazo",
    ),
    "ativo_circulante": ("ativo circulante",),
    "caixa_aplicacoes": ("ativo circulante", "disponivel"),
    "contas_receber_curto_prazo": ("ativo circulante",),
    "estoques": ("ativo circulante",),
    "exigivel_longo_prazo": ("passivo nao circulante", "exigivel longo prazo"),
    "bancos_longo_prazo": ("passivo nao circulante", "exigivel longo prazo"),
    "impostos_parcelados_diferidos_longo_prazo": (
        "passivo nao circulante",
        "exigivel longo prazo",
    ),
    "passivo_circulante": ("passivo circulante",),
    "bancos_curto_prazo": ("passivo circulante",),
    "fornecedores": ("passivo circulante",),
    "salarios_impostos": ("passivo circulante",),
}
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


def _normalize_group(value: Any) -> str:
    if value is None:
        return ""
    ascii_value = normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return ascii_value.lower().replace("-", " ").replace("_", " ")


def _account_matches_expected_group(
    account: dict[str, Any], expected_groups: tuple[str, ...]
) -> bool:
    group = _normalize_group(account.get("grupo_original"))
    return any(expected_group in group for expected_group in expected_groups)


def _filter_accounts_by_expected_group(
    field_name: str, accounts: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], tuple[str, ...]]:
    expected_groups = EXPECTED_GROUPS_BY_FIELD.get(field_name, ())
    if not expected_groups:
        return accounts, [], expected_groups
    if not any(_normalize_group(account.get("grupo_original")) for account in accounts):
        return accounts, [], expected_groups
    included = [
        account for account in accounts if _account_matches_expected_group(account, expected_groups)
    ]
    excluded = [
        account
        for account in accounts
        if not _account_matches_expected_group(account, expected_groups)
    ]
    return included, excluded, expected_groups


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

        included_accounts, excluded_accounts, expected_groups = _filter_accounts_by_expected_group(
            field_name, accounts
        )
        if expected_groups and not included_accounts:
            findings.append(
                RuleFinding(
                    rule_id=SUM_ACCOUNTS_RULE_ID,
                    field_path=field_path,
                    severity="warning",
                    outcome="not_assessable",
                    message=(
                        "Não foi possível recalcular a soma: nenhuma conta de origem "
                        "está no grupo contábil esperado para este campo."
                    ),
                    original_value=original_value,
                    inputs={
                        "tipo_obtencao": item.get("tipo_obtencao"),
                        "grupos_esperados": list(expected_groups),
                        "contas_origem": _serialize_accounts(accounts),
                    },
                )
            )
            continue

        account_values = [decimal_or_none(account.get("valor")) for account in included_accounts]
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
                        "grupos_esperados": list(expected_groups),
                        "contas_origem": _serialize_accounts(included_accounts),
                        "contas_origem_excluidas": _serialize_accounts(excluded_accounts),
                    },
                )
            )
            continue

        calculated_value = sum(account_values, Decimal("0"))
        difference = calculated_value - original_value
        inputs = {
            "tipo_obtencao": item.get("tipo_obtencao"),
            "grupos_esperados": list(expected_groups),
            "contas_origem": _serialize_accounts(included_accounts),
            "contas_origem_excluidas": _serialize_accounts(excluded_accounts),
        }
        if abs(difference) <= tolerance_amount:
            item["valor_validado"] = decimal_to_json(original_value)
            item["corrigido"] = False
            item["contas_origem_somadas"] = _serialize_accounts(included_accounts)
            item["contas_origem_excluidas"] = _serialize_accounts(excluded_accounts)
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
        item["contas_origem_somadas"] = _serialize_accounts(included_accounts)
        item["contas_origem_excluidas"] = _serialize_accounts(excluded_accounts)
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
