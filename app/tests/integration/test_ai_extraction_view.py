from datetime import timedelta
from decimal import Decimal

import pytest
from accounting.models import AccountingValidationRun
from accounting.services import validate_structured_balance
from companies.models import Company
from django.urls import reverse
from django.utils import timezone
from documents.models import BalanceDocument
from extraction.models import AIExtractionRun, ProcessingRun, RawExtraction


@pytest.mark.django_db
def test_authenticated_user_can_view_usage_and_estimated_cost(client, user, settings):
    settings.OPENAI_INPUT_USD_PER_MILLION_TOKENS = Decimal("1.25")
    settings.OPENAI_CACHED_INPUT_USD_PER_MILLION_TOKENS = Decimal("0.125")
    settings.OPENAI_OUTPUT_USD_PER_MILLION_TOKENS = Decimal("10")
    settings.USD_BRL_EXCHANGE_RATE = Decimal("5")
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    company = Company.objects.create(legal_name="ACME")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance.pdf",
        file="balance-documents/balance.pdf",
        file_uri="/media/balance-documents/balance.pdf",
        sha256="sha-ai-json",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")
    raw = RawExtraction.objects.create(
        document=document,
        processing_run=run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {
                    "tipo_documento": "balanco_patrimonial",
                    "periodo_original": "dez-23",
                },
                "campos_analise": {
                    "total_balanco": {"valor": 1000},
                    "passivo_circulante": {"valor": 700},
                    "exigivel_longo_prazo": {"valor": 0},
                    "patrimonio_liquido": {"valor": 300},
                    "liquidez_corrente": {"valor": 1.2},
                },
                "resumo_extracao": "Balanço extraído com sucesso.",
            }
        },
    )
    validate_structured_balance(raw)
    AIExtractionRun.objects.create(
        document=document,
        provider="openai",
        model_name="test-model",
        prompt_version="2026.06.23",
        token_usage={
            "input_tokens": 1000,
            "output_tokens": 500,
            "input_tokens_details": {"cached_tokens": 200},
        },
        status="succeeded",
    )
    client.force_login(user)

    response = client.get(reverse("document-ai-extraction", args=[document.id]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Resumo financeiro" in content
    assert "300" in content
    assert "1,2" in content
    assert "test-model" in content
    assert "US$ 0.006025" in content
    assert "R$ 0,030125" in content
    assert "Validação contábil automatizada" in content
    assert "Coerente" in content
    assert "Balanço extraído com sucesso." in content


@pytest.mark.django_db
def test_ai_extraction_view_displays_empty_validation_state(client, user):
    company = Company.objects.create(legal_name="Sem Validação LTDA")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance-empty.pdf",
        file="balance-documents/balance-empty.pdf",
        file_uri="/media/balance-documents/balance-empty.pdf",
        sha256="sha-ai-empty-validation",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")
    RawExtraction.objects.create(
        document=document,
        processing_run=run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {"periodo_original": "dez-23"},
                "campos_analise": {"patrimonio_liquido": {"valor": 300}},
            }
        },
    )
    client.force_login(user)

    response = client.get(reverse("document-ai-extraction", args=[document.id]))

    assert response.status_code == 200
    assert "A validação contábil ainda não foi executada" in response.content.decode()
    assert "Executar validação contábil" in response.content.decode()


@pytest.mark.django_db
def test_user_can_execute_accounting_validation_from_ai_extraction_page(
    client, user, settings
):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    company = Company.objects.create(legal_name="Validar Agora LTDA")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance-validate-now.pdf",
        file="balance-documents/balance-validate-now.pdf",
        file_uri="/media/balance-documents/balance-validate-now.pdf",
        sha256="sha-ai-validate-now",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")
    RawExtraction.objects.create(
        document=document,
        processing_run=run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {"tipo_documento": "balanco_patrimonial"},
                "campos_analise": {
                    "total_balanco": {"valor": 1000},
                    "passivo_circulante": {"valor": 700},
                    "exigivel_longo_prazo": {"valor": 0},
                    "patrimonio_liquido": {"valor": 300},
                },
            }
        },
    )
    client.force_login(user)

    response = client.post(reverse("document-validate-accounting", args=[document.id]))

    assert response.status_code == 302
    assert response.url == reverse("document-ai-extraction", args=[document.id])
    validation_run = AccountingValidationRun.objects.get(document=document)
    assert validation_run.status == AccountingValidationRun.Status.CONSISTENT

    response = client.get(reverse("document-ai-extraction", args=[document.id]))

    content = response.content.decode()
    assert "Coerente" in content
    assert "BALANCE_EQUATION_001" in content


@pytest.mark.django_db
def test_ai_extraction_view_displays_accounting_corrections(client, user, settings):
    settings.ACCOUNTING_VALIDATION_AMOUNT_TOLERANCE = Decimal("0.01")
    settings.ACCOUNTING_VALIDATION_RATIO_TOLERANCE = Decimal("0.01")
    company = Company.objects.create(legal_name="Correções LTDA")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance-corrections.pdf",
        file="balance-documents/balance-corrections.pdf",
        file_uri="/media/balance-documents/balance-corrections.pdf",
        sha256="sha-ai-corrections",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    run = ProcessingRun.objects.create(document=document, pipeline_version="2026.06")
    raw = RawExtraction.objects.create(
        document=document,
        processing_run=run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {
                    "tipo_documento": "balanco_patrimonial",
                    "periodo_original": "dez-23",
                },
                "campos_analise": {
                    "total_balanco": {"valor": 1000},
                    "passivo_circulante": {
                        "valor": 690,
                        "tipo_obtencao": "soma_contas",
                        "contas_origem": [{"descricao": "Banco", "valor": 700}],
                    },
                    "exigivel_longo_prazo": {"valor": 0},
                    "patrimonio_liquido": {"valor": 300},
                },
            }
        },
    )
    validate_structured_balance(raw)
    client.force_login(user)

    response = client.get(reverse("document-ai-extraction", args=[document.id]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "Correções aplicadas" in content
    assert "SUM_ACCOUNTS_001" in content
    assert "corrigido de 690" in content
    assert "700" in content


@pytest.mark.django_db
def test_ai_extraction_view_uses_latest_structured_extraction(client, user):
    company = Company.objects.create(legal_name="Reprocessada LTDA")
    document = BalanceDocument.objects.create(
        company=company,
        original_filename="balance-reprocessed.pdf",
        file="balance-documents/balance-reprocessed.pdf",
        file_uri="/media/balance-documents/balance-reprocessed.pdf",
        sha256="sha-ai-reprocessed",
        content_type="application/pdf",
        file_size_bytes=100,
        uploaded_by=user,
    )
    first_run = ProcessingRun.objects.create(document=document, pipeline_version="first")
    second_run = ProcessingRun.objects.create(document=document, pipeline_version="second")
    first_extraction = RawExtraction.objects.create(
        document=document,
        processing_run=first_run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {"periodo_original": "primeira"},
                "campos_analise": {"patrimonio_liquido": {"valor": 100}},
            }
        },
    )
    second_extraction = RawExtraction.objects.create(
        document=document,
        processing_run=second_run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {"periodo_original": "segunda"},
                "campos_analise": {"patrimonio_liquido": {"valor": 200}},
            }
        },
    )
    RawExtraction.objects.filter(pk=first_extraction.pk).update(
        created_at=timezone.now() - timedelta(days=1)
    )
    RawExtraction.objects.filter(pk=second_extraction.pk).update(created_at=timezone.now())
    client.force_login(user)

    response = client.get(reverse("document-ai-extraction", args=[document.id]))

    content = response.content.decode()
    assert response.status_code == 200
    assert "segunda" in content
    assert "200" in content
    assert "MultipleObjectsReturned" not in content
