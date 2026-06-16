from django import forms

from companies.models import ReportingPeriod
from standardization.models import StandardLineItem


class ReviewCorrectionForm(forms.Form):
    standard_line_item = forms.ModelChoiceField(queryset=StandardLineItem.objects.filter(is_active=True))
    value = forms.DecimalField(decimal_places=2, max_digits=18)
    currency = forms.CharField(max_length=10)
    reporting_period = forms.ModelChoiceField(queryset=ReportingPeriod.objects.all())
    reason = forms.CharField(widget=forms.Textarea)


class ReviewRejectForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea)
