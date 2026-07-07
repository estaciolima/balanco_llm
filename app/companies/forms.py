from django import forms

from companies.models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["legal_name", "display_name", "tax_identifier", "country", "status"]
