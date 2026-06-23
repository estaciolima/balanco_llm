import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from extraction.openai_balance import (
    EXTRACAO_ANALISE_BALANCO_SCHEMA,
    SYSTEM_PROMPT,
    build_user_prompt,
    extract_balance_data,
)


def _result_payload():
    item = {
        "valor": None,
        "tipo_obtencao": "nao_encontrado",
        "formula": None,
        "contas_origem": [],
        "valor_extraido_diretamente": None,
        "valor_calculado_pelas_contas": None,
        "diferenca_calculo_vs_extraido": None,
        "confianca": "baixa",
        "observacoes": None,
    }
    return {
        "metadados": {
            "tipo_documento": "balanco_patrimonial",
            "titulo": None,
            "razao_social": None,
            "cnpj": None,
            "periodo_inicio": None,
            "periodo_fim": None,
            "ano_referencia": None,
            "periodo_original": None,
            "data_emissao": None,
            "cidade_emissao": None,
            "moeda": "BRL",
            "escala_valores": "unidade",
        },
        "campos_analise": {
            name: item
            for name in EXTRACAO_ANALISE_BALANCO_SCHEMA["properties"]["campos_analise"][
                "properties"
            ]
        },
        "conferencia": {
            "ativo_total_extraido": None,
            "passivo_total_extraido": None,
            "total_balanco_declarado": None,
            "ativo_igual_passivo": None,
            "diferenca_ativo_passivo": None,
            "observacoes": None,
        },
        "contas_nao_utilizadas": [],
        "alertas": [],
        "resumo_extracao": "Sem dados.",
    }


def test_extract_balance_data_requests_strict_json_schema(settings):
    settings.OPENAI_BALANCE_EXTRACTION_MODEL = "test-model"
    payload = _result_payload()
    response = SimpleNamespace(output_text=json.dumps(payload), usage={"input_tokens": 12})
    create = MagicMock(return_value=response)
    client = SimpleNamespace(responses=SimpleNamespace(create=create))

    data, metadata = extract_balance_data("ATIVO CIRCULANTE 100", client=client)

    assert data == payload
    assert metadata["model"] == "test-model"
    assert metadata["token_usage"] == {"input_tokens": 12}
    assert create.call_args.kwargs["text"]["format"] == {
        "type": "json_schema",
        "name": "extracao_balanco",
        "schema": EXTRACAO_ANALISE_BALANCO_SCHEMA,
        "strict": True,
    }


def test_schema_and_prompts_match_the_notebook_exactly():
    notebook_path = Path(__file__).parents[3] / "notebooks" / "parsing_com_openai_api_3.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    namespace = {}
    for cell_index in (1, 2, 3):
        exec("".join(notebook["cells"][cell_index]["source"]), namespace)

    assert EXTRACAO_ANALISE_BALANCO_SCHEMA == namespace["EXTRACAO_ANALISE_BALANCO_SCHEMA"]
    assert SYSTEM_PROMPT == namespace["SYSTEM_PROMPT"]
    assert build_user_prompt("texto de teste") == namespace["build_user_prompt"]("texto de teste")
