from django.contrib import admin

from companies.models import Company, CompanyAlias, ReportingPeriod


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "display_name", "status", "updated_at")
    search_fields = ("legal_name", "display_name", "tax_identifier")


@admin.register(CompanyAlias)
class CompanyAliasAdmin(admin.ModelAdmin):
    list_display = ("alias", "company", "source", "created_at")
    search_fields = ("alias",)


@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
    list_display = ("company", "fiscal_year", "currency")
