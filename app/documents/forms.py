from django import forms
from django.utils import timezone


def _year_choices():
    current_year = timezone.now().year
    return [(year, str(year)) for year in range(current_year + 1, 1989, -1)]


class DocumentUploadForm(forms.Form):
    file = forms.FileField()
    fiscal_year = forms.TypedChoiceField(
        choices=_year_choices,
        coerce=int,
        label="Balance year",
    )
    notes = forms.CharField(required=False, widget=forms.Textarea)
