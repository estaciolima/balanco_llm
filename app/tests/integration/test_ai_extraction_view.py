from decimal import Decimal

import pytest
from companies.models import Company
from django.urls import reverse
from documents.models import BalanceDocument
from extraction.models import AIExtractionRun, ProcessingRun, RawExtraction


@pytest.mark.django_db
def test_authenticated_user_can_view_usage_and_estimated_cost(client, user, settings):
    settings.OPENAI_INPUT_USD_PER_MILLION_TOKENS = Decimal("1.25")
    settings.OPENAI_CACHED_INPUT_USD_PER_MILLION_TOKENS = Decimal("0.125")
    settings.OPENAI_OUTPUT_USD_PER_MILLION_TOKENS = Decimal("10")
    settings.USD_BRL_EXCHANGE_RATE = Decimal("5")
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
    RawExtraction.objects.create(
        document=document,
        processing_run=run,
        extraction_type=RawExtraction.ExtractionType.METADATA,
        source_method="openai_structured_output",
        content={
            "llm_output": {
                "metadados": {"periodo_original": "dez-23"},
                "campos_analise": {
                    "patrimonio_liquido": {"valor": 25355249},
                    "liquidez_corrente": {"valor": 1.2},
                },
                "resumo_extracao": "Balanço extraído com sucesso.",
            }
        },
    )
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

    assert response.status_code == 200
    assert "Resumo financeiro" in response.content.decode()
    assert "25.355.249" in response.content.decode()
    assert "1,2" in response.content.decode()
    assert "test-model" in response.content.decode()
    assert "US$ 0.006025" in response.content.decode()
    assert "R$ 0,030125" in response.content.decode()
    assert "Balanço extraído com sucesso." in response.content.decode()
