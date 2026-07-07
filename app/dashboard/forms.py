from django import forms


class DashboardFilterForm(forms.Form):
    start_year = forms.TypedChoiceField(required=False, coerce=int, empty_value=None, label="Start year")
    end_year = forms.TypedChoiceField(required=False, coerce=int, empty_value=None, label="End year")
    category = forms.CharField(required=False)
    currency = forms.CharField(required=False, max_length=10)

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        years = []
        if company is not None:
            years = list(
                company.reporting_periods.order_by("fiscal_year")
                .values_list("fiscal_year", flat=True)
                .distinct()
            )
        choices = [("", "All years")] + [(year, str(year)) for year in years]
        self.fields["start_year"].choices = choices
        self.fields["end_year"].choices = choices
