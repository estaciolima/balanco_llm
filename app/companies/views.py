from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from companies.forms import CompanyForm
from companies.models import Company


@login_required
def company_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    companies = Company.objects.all()
    if query:
        companies = companies.filter(Q(legal_name__icontains=query) | Q(display_name__icontains=query))
    if status:
        companies = companies.filter(status=status)
    return render(request, "companies/company_list.html", {"companies": companies, "query": query})


@login_required
def company_detail(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    return render(request, "companies/company_detail.html", {"company": company})


@login_required
def company_create(request):
    form = CompanyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        company = form.save()
        return redirect("company-detail", company_id=company.pk)
    return render(request, "companies/company_form.html", {"form": form})
