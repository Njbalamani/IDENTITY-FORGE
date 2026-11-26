from django import forms

from accounts.models import User
from certification.models import Campaign


class CampaignForm(forms.ModelForm):
    reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reviewers"].queryset = User.objects.filter(
            organization=organization, is_active=True
        )
        self.fields["due_date"].widget = forms.DateInput(attrs={"type": "date"})

    class Meta:
        model = Campaign
        fields = ["name", "due_date", "reviewers"]
