from django import forms

from analysis.models import RiskFinding


class FindingReviewForm(forms.ModelForm):
    class Meta:
        model = RiskFinding
        fields = ["status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
