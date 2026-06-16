from django.core.management.base import BaseCommand

from standardization.models import LineItemAlias, StandardLineItem


DEFAULT_LINE_ITEMS = [
    {
        "code": "equity",
        "display_name": "PATRIMONIO LIQUIDO",
        "category": StandardLineItem.Category.EQUITY,
        "line_type": StandardLineItem.LineType.SUBTOTAL,
        "display_level": 0,
        "sort_order": 10,
        "is_highlight": True,
        "aliases": ["PATRIMONIO LIQUIDO"],
    },
    {
        "code": "permanent_assets",
        "display_name": "PERMANENTE",
        "category": StandardLineItem.Category.ASSET,
        "line_type": StandardLineItem.LineType.SUBTOTAL,
        "display_level": 0,
        "sort_order": 20,
        "is_highlight": True,
        "aliases": ["PERMANENTE"],
    },
    {
        "code": "long_term_liabilities",
        "display_name": "EXIGIVEL LONGO PRAZO",
        "category": StandardLineItem.Category.LIABILITY,
        "line_type": StandardLineItem.LineType.SUBTOTAL,
        "display_level": 0,
        "sort_order": 30,
        "is_highlight": True,
        "aliases": ["EXIGIVEL LONGO PRAZO"],
    },
    {
        "code": "bank_long_term",
        "display_name": "Banco",
        "category": StandardLineItem.Category.LIABILITY,
        "display_level": 1,
        "sort_order": 40,
        "aliases": ["Banco", "Bancos LP", "Banco Longo Prazo"],
    },
    {
        "code": "deferred_taxes_long_term",
        "display_name": "Impostos Parcelados / Diferidos",
        "category": StandardLineItem.Category.LIABILITY,
        "display_level": 1,
        "sort_order": 50,
        "aliases": ["Impostos Parcelados / Diferidos", "Impostos Diferidos"],
    },
    {
        "code": "long_term_receivables_total",
        "display_name": "REALIZAVEL LONGO PRAZO",
        "category": StandardLineItem.Category.ASSET,
        "line_type": StandardLineItem.LineType.SUBTOTAL,
        "display_level": 0,
        "sort_order": 60,
        "is_highlight": True,
        "aliases": ["REALIZAVEL LONGO PRAZO"],
    },
    {
        "code": "customer_receivables_long_term",
        "display_name": "Contas a Receber Clientes LP",
        "category": StandardLineItem.Category.ASSET,
        "display_level": 1,
        "sort_order": 70,
        "aliases": ["Contas a Receber Clientes LP", "Clientes LP"],
    },
    {
        "code": "inventory_long_term",
        "display_name": "Estoques LP",
        "category": StandardLineItem.Category.ASSET,
        "display_level": 1,
        "sort_order": 80,
        "aliases": ["Estoques LP"],
    },
    {
        "code": "related_party_receivables",
        "display_name": "Contas Receber Emp Ligadas/Socios",
        "category": StandardLineItem.Category.ASSET,
        "display_level": 1,
        "sort_order": 90,
        "aliases": ["Contas Receber Emp Ligadas/Socios", "Partes Relacionadas"],
    },
    {
        "code": "recoverable_taxes_long_term",
        "display_name": "Impostos a Recuperar/ Diferidos",
        "category": StandardLineItem.Category.ASSET,
        "display_level": 1,
        "sort_order": 100,
        "aliases": ["Impostos a Recuperar/ Diferidos", "Impostos a Recuperar"],
    },
    {
        "code": "current_assets",
        "display_name": "ATIVO CIRCULANTE",
        "category": StandardLineItem.Category.ASSET,
        "line_type": StandardLineItem.LineType.SUBTOTAL,
        "display_level": 0,
        "sort_order": 110,
        "is_highlight": True,
        "aliases": ["ATIVO CIRCULANTE", "CIRCULANTE"],
    },
    {
        "code": "cash_and_equivalents",
        "display_name": "Caixa + Aplicacoes",
        "category": StandardLineItem.Category.ASSET,
        "display_level": 1,
        "sort_order": 120,
        "source_account_patterns": ["1.1.01*"],
        "aliases": [
            "Caixa + Aplicacoes",
            "Caixa e Equivalente de Caixa",
            "CAIXA E EQUIVALENTE DE CAIXA",
            "Disponibilidades",
        ],
    },
    {
        "code": "accounts_receivable",
        "display_name": "Contas a Receber",
        "category": StandardLineItem.Category.ASSET,
        "display_level": 1,
        "sort_order": 130,
        "aliases": ["Contas a Receber", "Clientes"],
    },
    {
        "code": "inventory",
        "display_name": "Estoques",
        "category": StandardLineItem.Category.ASSET,
        "display_level": 1,
        "sort_order": 140,
        "aliases": ["Estoques", "ESTOQUES"],
    },
    {
        "code": "current_liabilities",
        "display_name": "PASSIVO CIRCULANTE",
        "category": StandardLineItem.Category.LIABILITY,
        "line_type": StandardLineItem.LineType.SUBTOTAL,
        "display_level": 0,
        "sort_order": 150,
        "is_highlight": True,
        "aliases": ["PASSIVO CIRCULANTE"],
    },
    {
        "code": "short_term_banks",
        "display_name": "Bancos - Curto Prazo",
        "category": StandardLineItem.Category.LIABILITY,
        "display_level": 1,
        "sort_order": 160,
        "aliases": ["Bancos - Curto Prazo", "Bancos CP"],
    },
    {
        "code": "suppliers",
        "display_name": "Fornecedores",
        "category": StandardLineItem.Category.LIABILITY,
        "display_level": 1,
        "sort_order": 170,
        "aliases": ["Fornecedores"],
    },
    {
        "code": "salaries_and_taxes",
        "display_name": "Salarios e Impostos",
        "category": StandardLineItem.Category.LIABILITY,
        "display_level": 1,
        "sort_order": 180,
        "aliases": ["Salarios e Impostos"],
    },
    {
        "code": "balance_total",
        "display_name": "TOTAL DO BALANCO",
        "category": StandardLineItem.Category.OTHER,
        "line_type": StandardLineItem.LineType.TOTAL,
        "display_level": 0,
        "sort_order": 190,
        "is_highlight": True,
        "aliases": ["TOTAL DO BALANCO"],
    },
    {
        "code": "average_receivables_days",
        "display_name": "Prazo medio de recebimentos",
        "category": StandardLineItem.Category.OTHER,
        "line_type": StandardLineItem.LineType.RATIO,
        "display_level": 0,
        "sort_order": 200,
        "aliases": ["Prazo medio de recebimentos"],
    },
    {
        "code": "current_liquidity",
        "display_name": "Liquidez Corrente (AC/PC)",
        "category": StandardLineItem.Category.OTHER,
        "statement_section": StandardLineItem.StatementSection.LIQUIDITY,
        "line_type": StandardLineItem.LineType.RATIO,
        "display_level": 1,
        "sort_order": 210,
        "aliases": ["Liquidez Corrente"],
    },
    {
        "code": "quick_liquidity",
        "display_name": "Liquidez Seca (AC-E/PC)",
        "category": StandardLineItem.Category.OTHER,
        "statement_section": StandardLineItem.StatementSection.LIQUIDITY,
        "line_type": StandardLineItem.LineType.RATIO,
        "display_level": 1,
        "sort_order": 220,
        "aliases": ["Liquidez Seca"],
    },
    {
        "code": "general_liquidity",
        "display_name": "Liquidez Geral (AC+RLP/PC+ELP)",
        "category": StandardLineItem.Category.OTHER,
        "statement_section": StandardLineItem.StatementSection.LIQUIDITY,
        "line_type": StandardLineItem.LineType.RATIO,
        "display_level": 1,
        "sort_order": 230,
        "aliases": ["Liquidez Geral"],
    },
]


class Command(BaseCommand):
    help = "Load standardized balance presentation line items"

    def handle(self, *args, **options):
        for item in DEFAULT_LINE_ITEMS:
            aliases = item.get("aliases", [])
            line_item, _created = StandardLineItem.objects.update_or_create(
                code=item["code"],
                defaults={
                    key: value for key, value in item.items() if key not in {"code", "aliases"}
                },
            )
            for alias in aliases:
                LineItemAlias.objects.get_or_create(
                    standard_line_item=line_item,
                    alias_text=alias,
                    language="pt",
                )
        self.stdout.write(self.style.SUCCESS("Loaded standard line items"))
