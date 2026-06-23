from companies.models import Company
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from dashboard.forms import DashboardFilterForm
from dashboard.serializers import build_plotly_series
from dashboard.services import get_company_ai_dashboard_matrix, get_company_dashboard_matrix


@login_required
def company_dashboard(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    form = DashboardFilterForm(request.GET, company=company)
    form.is_valid()
    matrix = get_company_ai_dashboard_matrix(
        company=company,
        start_year=form.cleaned_data.get("start_year"),
        end_year=form.cleaned_data.get("end_year"),
        currency=form.cleaned_data.get("currency", ""),
    )
    if not matrix["periods"]:
        matrix = get_company_dashboard_matrix(
            company=company,
            start_year=form.cleaned_data.get("start_year"),
            end_year=form.cleaned_data.get("end_year"),
            category=form.cleaned_data.get("category", ""),
            currency=form.cleaned_data.get("currency", ""),
        )
    rows = matrix["flat_rows"]
    chart_series = build_plotly_series(rows)
    return render(
        request,
        "dashboard/company_dashboard.html",
        {
            "company": company,
            "form": form,
            "rows": rows,
            "matrix": matrix,
            "chart_series": chart_series,
        },
    )
