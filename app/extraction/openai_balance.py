"""OpenAI-backed structured extraction for Brazilian balance sheets.

The API key is read by the official OpenAI client from ``OPENAI_API_KEY``.
Calls are opt-in through ``OPENAI_BALANCE_EXTRACTION_ENABLED`` so normal
document processing remains local and deterministic by default.
"""
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
from typing import Any

from django.conf import settings

CONTA_ORIGEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "codigo": {
            "type": ["string", "null"],
            "description": "Código da conta contábil, quando existir. Exemplo: 2.1.05.",
        },
        "descricao": {
            "type": ["string", "null"],
            "description": "Descrição da conta conforme aparece no documento.",
        },
        "valor": {
            "type": ["number", "null"],
            "description": "Valor numérico da conta, sem separador de milhar.",
        },
        "natureza": {
            "type": ["string", "null"],
            "enum": ["D", "C", None],
            "description": "Natureza da conta, se informada: D para débito, C para crédito.",
        },
        "grupo_original": {
            "type": ["string", "null"],
            "description": "Grupo onde a conta aparece. Exemplo: Ativo Circulante, Passivo Circulante.",
        },
        "evidencia_textual": {
            "type": ["string", "null"],
            "description": "Trecho do texto extraído do PDF que justifica a conta.",
        },
    },
    "required": ["codigo", "descricao", "valor", "natureza", "grupo_original", "evidencia_textual"],
}


ITEM_ANALISE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "valor": {
            "type": ["number", "null"],
            "description": "Valor final do campo analisado. Use null se não for possível encontrar ou calcular com segurança.",
        },
        "tipo_obtencao": {
            "type": "string",
            "enum": [
                "extraido_diretamente",
                "soma_contas",
                "calculo_indice",
                "premissa_externa",
                "nao_encontrado",
                "nao_calculavel",
                "ambiguidade",
            ],
        },
        "formula": {
            "type": ["string", "null"],
            "description": "Fórmula usada, quando aplicável. Exemplo: Ativo Circulante / Passivo Circulante.",
        },
        "contas_origem": {
            "type": "array",
            "items": CONTA_ORIGEM_SCHEMA,
            "description": "Contas do documento usadas para chegar ao valor final.",
        },
        "valor_extraido_diretamente": {
            "type": ["number", "null"],
            "description": "Valor encontrado diretamente no documento, se houver.",
        },
        "valor_calculado_pelas_contas": {
            "type": ["number", "null"],
            "description": "Valor obtido pela soma das contas de origem ou pelo cálculo indicado.",
        },
        "diferenca_calculo_vs_extraido": {
            "type": ["number", "null"],
            "description": "Diferença entre valor calculado e valor extraído diretamente, quando aplicável.",
        },
        "confianca": {"type": "string", "enum": ["alta", "media", "baixa"]},
        "observacoes": {"type": ["string", "null"]},
    },
    "required": [
        "valor",
        "tipo_obtencao",
        "formula",
        "contas_origem",
        "valor_extraido_diretamente",
        "valor_calculado_pelas_contas",
        "diferenca_calculo_vs_extraido",
        "confianca",
        "observacoes",
    ],
}


ALERTA_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "tipo": {
            "type": "string",
            "enum": [
                "campo_nao_encontrado",
                "campo_nao_calculavel",
                "valor_ambiguo",
                "hierarquia_ambigua",
                "possivel_conta_nao_incluida",
                "possivel_erro_extracao_pdf",
                "divergencia_total",
                "outro",
            ],
        },
        "campo_relacionado": {"type": ["string", "null"]},
        "mensagem": {"type": "string"},
        "evidencia_textual": {"type": ["string", "null"]},
    },
    "required": ["tipo", "campo_relacionado", "mensagem", "evidencia_textual"],
}


EXTRACAO_ANALISE_BALANCO_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "metadados": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "tipo_documento": {
                    "type": "string",
                    "enum": ["balanco_patrimonial", "dre", "balancete", "outros"],
                },
                "titulo": {"type": ["string", "null"]},
                "razao_social": {"type": ["string", "null"]},
                "cnpj": {"type": ["string", "null"]},
                "periodo_inicio": {
                    "type": ["string", "null"],
                    "description": "Data em formato YYYY-MM-DD, ou null.",
                },
                "periodo_fim": {
                    "type": ["string", "null"],
                    "description": "Data em formato YYYY-MM-DD, ou null.",
                },
                "ano_referencia": {"type": ["integer", "null"]},
                "periodo_original": {"type": ["string", "null"]},
                "data_emissao": {
                    "type": ["string", "null"],
                    "description": "Data em formato YYYY-MM-DD, ou null.",
                },
                "cidade_emissao": {"type": ["string", "null"]},
                "moeda": {"type": ["string", "null"], "description": "Exemplo: BRL."},
                "escala_valores": {
                    "type": ["string", "null"],
                    "enum": ["unidade", "milhares", "milhoes", None],
                },
            },
            "required": [
                "tipo_documento",
                "titulo",
                "razao_social",
                "cnpj",
                "periodo_inicio",
                "periodo_fim",
                "ano_referencia",
                "periodo_original",
                "data_emissao",
                "cidade_emissao",
                "moeda",
                "escala_valores",
            ],
        },
        "campos_analise": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "patrimonio_liquido": ITEM_ANALISE_SCHEMA,
                "permanente": ITEM_ANALISE_SCHEMA,
                "exigivel_longo_prazo": ITEM_ANALISE_SCHEMA,
                "bancos_longo_prazo": ITEM_ANALISE_SCHEMA,
                "impostos_parcelados_diferidos_longo_prazo": ITEM_ANALISE_SCHEMA,
                "realizavel_longo_prazo": ITEM_ANALISE_SCHEMA,
                "contas_receber_clientes_longo_prazo": ITEM_ANALISE_SCHEMA,
                "estoques_longo_prazo": ITEM_ANALISE_SCHEMA,
                "contas_receber_empresas_ligadas_socios": ITEM_ANALISE_SCHEMA,
                "impostos_recuperar_diferidos_ativo": ITEM_ANALISE_SCHEMA,
                "ativo_circulante": ITEM_ANALISE_SCHEMA,
                "caixa_aplicacoes": ITEM_ANALISE_SCHEMA,
                "contas_receber_curto_prazo": ITEM_ANALISE_SCHEMA,
                "estoques": ITEM_ANALISE_SCHEMA,
                "passivo_circulante": ITEM_ANALISE_SCHEMA,
                "bancos_curto_prazo": ITEM_ANALISE_SCHEMA,
                "fornecedores": ITEM_ANALISE_SCHEMA,
                "salarios_impostos": ITEM_ANALISE_SCHEMA,
                "total_balanco": ITEM_ANALISE_SCHEMA,
                "prazo_medio_recebimentos": ITEM_ANALISE_SCHEMA,
                "liquidez_corrente": ITEM_ANALISE_SCHEMA,
                "liquidez_seca": ITEM_ANALISE_SCHEMA,
                "liquidez_geral": ITEM_ANALISE_SCHEMA,
            },
            "required": [
                "patrimonio_liquido",
                "permanente",
                "exigivel_longo_prazo",
                "bancos_longo_prazo",
                "impostos_parcelados_diferidos_longo_prazo",
                "realizavel_longo_prazo",
                "contas_receber_clientes_longo_prazo",
                "estoques_longo_prazo",
                "contas_receber_empresas_ligadas_socios",
                "impostos_recuperar_diferidos_ativo",
                "ativo_circulante",
                "caixa_aplicacoes",
                "contas_receber_curto_prazo",
                "estoques",
                "passivo_circulante",
                "bancos_curto_prazo",
                "fornecedores",
                "salarios_impostos",
                "total_balanco",
                "prazo_medio_recebimentos",
                "liquidez_corrente",
                "liquidez_seca",
                "liquidez_geral",
            ],
        },
        "conferencia": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "ativo_total_extraido": {"type": ["number", "null"]},
                "passivo_total_extraido": {"type": ["number", "null"]},
                "total_balanco_declarado": {"type": ["number", "null"]},
                "ativo_igual_passivo": {"type": ["boolean", "null"]},
                "diferenca_ativo_passivo": {"type": ["number", "null"]},
                "observacoes": {"type": ["string", "null"]},
            },
            "required": [
                "ativo_total_extraido",
                "passivo_total_extraido",
                "total_balanco_declarado",
                "ativo_igual_passivo",
                "diferenca_ativo_passivo",
                "observacoes",
            ],
        },
        "contas_nao_utilizadas": {
            "type": "array",
            "items": CONTA_ORIGEM_SCHEMA,
            "description": "Contas identificadas no balanço, mas que não foram usadas em nenhum campo da análise.",
        },
        "alertas": {"type": "array", "items": ALERTA_SCHEMA},
        "resumo_extracao": {"type": "string"},
    },
    "required": [
        "metadados",
        "campos_analise",
        "conferencia",
        "contas_nao_utilizadas",
        "alertas",
        "resumo_extracao",
    ],
}
SYSTEM_PROMPT = """
Você é um especialista em extração e classificação de informações de balanços patrimoniais brasileiros.

Sua tarefa é analisar o texto extraído de um PDF contábil e preencher um JSON estruturado com os campos de análise solicitados.

Você deve:
- Usar apenas informações presentes no texto fornecido.
- Não inventar valores.
- Não estimar valores ausentes.
- Preservar valores monetários com centavos quando estiverem disponíveis.
- Converter números brasileiros para formato numérico JSON. Exemplo: "137.858.000,74" deve virar 137858000.74.
- Identificar contas que devem ser agrupadas em uma mesma categoria de análise.
- Para cada campo, informar as contas de origem usadas.
- Para cada campo, informar se o valor foi extraído diretamente, calculado por soma de contas, calculado como índice, veio de premissa externa, não foi encontrado, não é calculável ou ficou ambíguo.
- Quando um campo não puder ser encontrado, retornar valor null e tipo_obtencao "nao_encontrado".
- Quando um campo depender de informação que não está no balanço patrimonial, retornar valor null e tipo_obtencao "nao_calculavel".
- Quando houver dúvida sobre a classificação de uma conta, usar confiança "baixa" ou "media" e registrar alerta.
- Não incluir uma mesma conta de origem em dois campos de análise incompatíveis.
- Incluir em contas_nao_utilizadas as contas identificadas no balanço que não foram usadas em nenhum campo da análise.
- Retornar somente JSON válido conforme o schema fornecido.

Regras de classificação dos campos:

1. patrimonio_liquido:
Use o grupo Patrimônio Líquido, Capital, Reservas, Lucros/Prejuízos acumulados ou equivalente. Se houver o total do grupo Patrimônio Líquido, prefira o total diretamente declarado.

2. permanente:
Use o grupo Permanente, quando existir. Caso não exista com esse nome, considere contas como Imobilizado, Intangível, Investimentos e Ativos de direito de uso, desde que estejam no ativo não circulante e tenham natureza de ativo permanente. Informe a composição nas contas de origem.

3. exigivel_longo_prazo:
Use o Passivo Não Circulante ou Exigível a Longo Prazo.

4. bancos_longo_prazo:
Use empréstimos, financiamentos, bancos ou instrumentos similares classificados no Passivo Não Circulante ou Exigível a Longo Prazo.

5. impostos_parcelados_diferidos_longo_prazo:
Use contas tributárias de longo prazo no passivo, como Parcelamento de Tributos, Obrigações Tributárias, Impostos Diferidos, Provisões Fiscais/Trabalhistas/Cíveis, tributos a recolher ou equivalentes classificados no Passivo Não Circulante. Não misture com impostos a recuperar do ativo.

6. realizavel_longo_prazo:
Use o Ativo Não Circulante ou Realizável a Longo Prazo.

7. contas_receber_clientes_longo_prazo:
Use Contas a Receber de Clientes classificadas no Ativo Não Circulante ou Realizável a Longo Prazo.

8. estoques_longo_prazo:
Use Estoques classificados no longo prazo, se existirem.

9. contas_receber_empresas_ligadas_socios:
Use Partes Relacionadas, Empresas Ligadas, Sócios, Acionistas ou contas semelhantes dentro de Ativo Não Circulante ou Realizável a Longo Prazo.

10. impostos_recuperar_diferidos_ativo:
Use tributos a recuperar, impostos a recuperar, impostos diferidos, créditos fiscais ou valores restituíveis classificados no Ativo Não Circulante ou Realizável a Longo Prazo. **NÃO inclua impostos no ATIVO CIRCULANTE** .

11. ativo_circulante:
Use o total do Ativo Circulante.

12. caixa_aplicacoes:
Use Caixa, Bancos, Disponibilidades, Equivalentes de Caixa, Aplicações Financeiras e Instrumentos Financeiros classificados no Ativo Circulante.

13. contas_receber_curto_prazo:
Use Contas a Receber de Clientes no Ativo Circulante.

14. estoques:
Use Estoques no Ativo Circulante. Se não houver conta de estoques, retornar valor null ou 0 somente se a ausência indicar claramente inexistência. Preferir null com alerta quando não for possível ter certeza.

15. passivo_circulante:
Use o total do Passivo Circulante.

16. bancos_curto_prazo:
Use Empréstimos, Financiamentos, Bancos ou instrumentos similares classificados no Passivo Circulante.

17. fornecedores:
Use Fornecedores classificados no Passivo Circulante, **NÃO INCLUA** Fornecedores de Longo Prazo.

18. salarios_impostos:
Use contas de obrigações sociais, trabalhistas e tributárias de curto prazo, como salários, encargos sociais, obrigações sociais e trabalhistas, provisões de encargos sociais e trabalhistas, obrigações tributárias, tributos a recolher, retenções na fonte e equivalentes no Passivo Circulante.

19. total_balanco:
Use o total declarado do ativo/passivo ou o total do balanço, quando informado.

20. prazo_medio_recebimentos:
Só calcule se o documento trouxer as informações necessárias, como receita/vendas/faturamento e contas a receber, ou se o próprio prazo estiver declarado. Caso contrário, retorne null e tipo_obtencao "nao_calculavel".

21. liquidez_corrente:
Calcule como Ativo Circulante / Passivo Circulante, se ambos existirem.

22. liquidez_seca:
Calcule como (Ativo Circulante - Estoques) / Passivo Circulante. Se Estoques não for encontrado, explique a premissa adotada. Não assuma estoque zero sem registrar observação.

23. liquidez_geral:
Calcule como (Ativo Circulante + Realizável Longo Prazo) / (Passivo Circulante + Exigível Longo Prazo), se os componentes existirem.

Para todos os índices, preencher:
- valor
- tipo_obtencao como "calculo_indice"
- formula
- contas_origem com os componentes usados
- observacoes explicando qualquer premissa
"""


def build_user_prompt(pdf_text: str) -> str:
    return f"""
Extraia os campos de análise de balanço patrimonial a partir do texto abaixo.

O objetivo é preencher os mesmos campos da tabela de análise financeira, incluindo agrupamentos como:
- Caixa + Aplicações
- Bancos curto prazo
- Bancos longo prazo
- Salários e Impostos
- Impostos Parcelados / Diferidos
- Liquidez Corrente
- Liquidez Seca
- Liquidez Geral

Instruções específicas:
- Retorne somente o JSON válido no schema definido.
- Não invente informações ausentes.
- Para cada campo, informe quais contas do balanço foram usadas.
- Quando um campo for calculado por soma de contas, mostre as contas de origem.
- Quando um índice for calculado, informe a fórmula.
- Quando um campo não puder ser calculado apenas com o balanço patrimonial, retorne null e explique em observacoes.
- Preserve centavos quando existirem.
- Use confiança baixa ou média quando houver ambiguidade de classificação.

Texto do PDF:

\"\"\"
{pdf_text}
\"\"\"
"""


PROMPT_VERSION = "2026.06.23"


def extract_balance_data(
    pdf_text: str, *, client=None, model: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the structured extraction and auditable request metadata."""
    if not pdf_text.strip():
        raise ValueError("N?o ? poss?vel consultar a LLM sem texto extra?do do PDF.")
    if client is None:
        from openai import OpenAI

        client = OpenAI()
    model = model or settings.OPENAI_BALANCE_EXTRACTION_MODEL
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(pdf_text)},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "extracao_balanco",
                "schema": EXTRACAO_ANALISE_BALANCO_SCHEMA,
                "strict": True,
            }
        },
    )
    data = json.loads(response.output_text)
    usage = getattr(response, "usage", None)
    usage_data = usage.model_dump() if hasattr(usage, "model_dump") else (usage or {})
    metadata = {
        "provider": "openai",
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "token_usage": usage_data,
        "output_hash": hashlib.sha256(response.output_text.encode()).hexdigest(),
    }
    return data, metadata
