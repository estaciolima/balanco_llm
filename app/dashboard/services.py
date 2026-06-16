from standardization.models import StandardizedBalanceValue


def get_company_dashboard_rows(*, company, start_year=None, end_year=None, category="", currency=""):
    queryset = (
        StandardizedBalanceValue.objects.select_related("reporting_period", "standard_line_item")
        .filter(
            company=company,
            approval_status=StandardizedBalanceValue.ApprovalStatus.APPROVED,
        )
        .order_by("standard_line_item__sort_order", "reporting_period__fiscal_year")
    )
    if start_year:
        queryset = queryset.filter(reporting_period__fiscal_year__gte=start_year)
    if end_year:
        queryset = queryset.filter(reporting_period__fiscal_year__lte=end_year)
    if category:
        queryset = queryset.filter(standard_line_item__category=category)
    if currency:
        queryset = queryset.filter(currency__iexact=currency)

    rows = []
    for value in queryset:
        rows.append(
            {
                "value_id": str(value.pk),
                "year_label": str(value.reporting_period.fiscal_year),
                "fiscal_year": value.reporting_period.fiscal_year,
                "standard_line_item_code": value.standard_line_item.code,
                "standard_line_item": value.standard_line_item.display_name,
                "category": value.standard_line_item.category,
                "section": value.standard_line_item.statement_section,
                "line_type": value.standard_line_item.line_type,
                "display_level": value.standard_line_item.display_level,
                "is_highlight": value.standard_line_item.is_highlight,
                "sort_order": value.standard_line_item.sort_order,
                "value": value.value,
                "currency": value.currency,
                "document_id": "",
            }
        )
    return rows


def get_company_dashboard_matrix(*, company, start_year=None, end_year=None, category="", currency=""):
    flat_rows = get_company_dashboard_rows(
        company=company,
        start_year=start_year,
        end_year=end_year,
        category=category,
        currency=currency,
    )
    periods = []
    period_keys = set()
    grouped = {}

    for row in flat_rows:
        period_key = row["year_label"]
        if period_key not in period_keys:
            period_keys.add(period_key)
            periods.append({"label": row["year_label"], "fiscal_year": row["fiscal_year"]})

        item_key = row["standard_line_item_code"]
        grouped.setdefault(
            item_key,
            {
                "code": item_key,
                "label": row["standard_line_item"],
                "category": row["category"],
                "section": row["section"],
                "line_type": row["line_type"],
                "display_level": row["display_level"],
                "is_highlight": row["is_highlight"],
                "sort_order": row["sort_order"],
                "values": {},
            },
        )
        grouped[item_key]["values"][period_key] = {
            "value": row["value"],
            "currency": row["currency"],
            "document_id": row["document_id"],
        }

    periods.sort(key=lambda item: item["fiscal_year"])
    matrix_rows = sorted(grouped.values(), key=lambda item: item["sort_order"])
    return {"periods": periods, "rows": matrix_rows, "flat_rows": flat_rows}
