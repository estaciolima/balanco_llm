from __future__ import annotations

import time
from collections import Counter
from decimal import Decimal
from typing import Any

from audit.services import record_audit_event
from django.conf import settings
from django.db import transaction
from extraction.models import RawExtraction

from accounting.models import AccountingValidationFinding, AccountingValidationRun
from accounting.rules import (
    SUPPORTED_BALANCE_DOCUMENT_TYPES,
    RuleFinding,
    apply_sum_account_corrections,
    decimal_to_json,
    evaluate_balance_equation,
)


def _finding_to_model_kwargs(finding: RuleFinding) -> dict[str, Any]:
    return {
        "rule_id": finding.rule_id,
        "field_path": finding.field_path,
        "severity": finding.severity,
        "outcome": finding.outcome,
        "message": finding.message,
        "original_value": finding.original_value,
        "calculated_value": finding.calculated_value,
        "difference": finding.difference,
        "inputs": finding.inputs or {},
    }


def _finding_to_json(finding: RuleFinding) -> dict[str, Any]:
    return {
        "rule_id": finding.rule_id,
        "field_path": finding.field_path,
        "severity": finding.severity,
        "outcome": finding.outcome,
        "message": finding.message,
        "original_value": decimal_to_json(finding.original_value),
        "calculated_value": decimal_to_json(finding.calculated_value),
        "difference": decimal_to_json(finding.difference),
        "inputs": finding.inputs or {},
    }


def _summarize(findings: list[RuleFinding]) -> dict[str, dict[str, int]]:
    return {
        "by_outcome": dict(Counter(finding.outcome for finding in findings)),
        "by_severity": dict(Counter(finding.severity for finding in findings)),
    }


def _status_for(findings: list[RuleFinding]) -> str:
    if not findings:
        return AccountingValidationRun.Status.NOT_ASSESSABLE
    if any(finding.outcome == "failed" and finding.severity == "high" for finding in findings):
        return AccountingValidationRun.Status.INCONSISTENT
    assessable = [finding for finding in findings if finding.outcome != "not_assessable"]
    if not assessable:
        return AccountingValidationRun.Status.NOT_ASSESSABLE
    if any(finding.outcome in {"corrected", "failed", "not_assessable"} for finding in findings):
        return AccountingValidationRun.Status.WARNING
    return AccountingValidationRun.Status.CONSISTENT


def _audit_after(
    run: AccountingValidationRun, finding: RuleFinding | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "validation_run_id": str(run.id),
        "raw_extraction_id": str(run.raw_extraction_id),
        "status": run.status,
    }
    if finding is not None:
        payload.update(_finding_to_json(finding))
        payload["corrected_value"] = decimal_to_json(finding.calculated_value)
        payload["explanation"] = finding.message
    return payload


def _create_audit_events(
    run: AccountingValidationRun, findings: list[RuleFinding], actor_user=None
) -> None:
    record_audit_event(
        event_type="accounting.validation.started",
        target_type="BalanceDocument",
        target_id=str(run.document_id),
        actor_user=actor_user,
        after={"validation_run_id": str(run.id), "raw_extraction_id": str(run.raw_extraction_id)},
        reason="Accounting validation started.",
    )
    record_audit_event(
        event_type="accounting.validation.completed",
        target_type="BalanceDocument",
        target_id=str(run.document_id),
        actor_user=actor_user,
        after=_audit_after(run),
        reason="Accounting validation completed.",
    )
    for finding in findings:
        if finding.outcome == "corrected":
            record_audit_event(
                event_type="accounting.validation.correction_applied",
                target_type="BalanceDocument",
                target_id=str(run.document_id),
                actor_user=actor_user,
                before={
                    "field_path": finding.field_path,
                    "original_value": decimal_to_json(finding.original_value),
                },
                after=_audit_after(run, finding),
                reason=finding.message,
            )
        elif finding.outcome == "failed" and finding.severity == "high":
            record_audit_event(
                event_type="accounting.validation.inconsistency_detected",
                target_type="BalanceDocument",
                target_id=str(run.document_id),
                actor_user=actor_user,
                after=_audit_after(run, finding),
                reason=finding.message,
            )


def validate_structured_balance(
    raw_extraction: RawExtraction, *, actor_user=None
) -> AccountingValidationRun:
    started = time.perf_counter()
    tolerance_amount: Decimal = settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE
    tolerance_ratio: Decimal = settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE
    content = raw_extraction.content or {}
    llm_output = content.get("llm_output") if isinstance(content, dict) else None
    findings: list[RuleFinding] = []

    if not isinstance(llm_output, dict):
        validated_output: dict[str, Any] = {}
        findings.append(
            RuleFinding(
                rule_id="STRUCTURED_OUTPUT_001",
                field_path="llm_output",
                severity="warning",
                outcome="not_assessable",
                message="Não foi possível validar: saída estruturada da IA ausente.",
            )
        )
    else:
        metadata = llm_output.get("metadados", {})
        document_type = metadata.get("tipo_documento") if isinstance(metadata, dict) else None
        if document_type not in SUPPORTED_BALANCE_DOCUMENT_TYPES:
            validated_output = llm_output.copy()
            findings.append(
                RuleFinding(
                    rule_id="SUPPORTED_DOCUMENT_001",
                    field_path="metadados.tipo_documento",
                    severity="warning",
                    outcome="not_assessable",
                    message="Documento fora do escopo do MVP de validação de balanço patrimonial.",
                    inputs={"tipo_documento": document_type},
                )
            )
        else:
            validated_output, sum_findings = apply_sum_account_corrections(
                llm_output, tolerance_amount
            )
            findings.extend(sum_findings)
            findings.append(evaluate_balance_equation(validated_output, tolerance_amount))

    status = _status_for(findings)
    summary = _summarize(findings)
    duration_ms = int((time.perf_counter() - started) * 1000)
    validated_output.setdefault("validacao_contabil", {})
    validated_output["validacao_contabil"].update(
        {
            "status": status,
            "summary": summary,
            "findings": [_finding_to_json(finding) for finding in findings],
        }
    )

    with transaction.atomic():
        run = AccountingValidationRun.objects.create(
            document=raw_extraction.document,
            raw_extraction=raw_extraction,
            ai_extraction_run=raw_extraction.document.ai_extraction_runs.order_by("-created_at").first(),
            status=status,
            tolerance_amount=tolerance_amount,
            tolerance_ratio=tolerance_ratio,
            summary=summary,
            validated_output=validated_output,
            duration_ms=duration_ms,
        )
        AccountingValidationFinding.objects.bulk_create(
            [
                AccountingValidationFinding(validation_run=run, **_finding_to_model_kwargs(finding))
                for finding in findings
            ]
        )
        validated_output["validacao_contabil"]["run_id"] = str(run.id)
        run.validated_output = validated_output
        run.save(update_fields=["validated_output"])
        _create_audit_events(run, findings, actor_user=actor_user)
    return run
