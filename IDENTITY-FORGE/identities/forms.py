from django import forms

from identities.models import IdentityProfile, Team


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "description", "parent"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class IdentityProfileForm(forms.ModelForm):
    class Meta:
        model = IdentityProfile
        fields = [
            "team",
            "employee_id",
            "department",
            "title",
            "status",
            "mfa_enabled",
            "session_timeout_minutes",
            "last_activity_at",
        ]
        widgets = {"last_activity_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
