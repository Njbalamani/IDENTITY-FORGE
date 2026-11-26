from django import forms

from access.models import AccessReview, Permission, Role, RoleAssignment


class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = ["code", "name", "category", "description", "risk_weight", "is_high_risk"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            "name",
            "code",
            "description",
            "permissions",
            "inherits",
            "conflicts",
            "is_privileged",
            "risk_weight",
        ]

    def __init__(self, organization=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            self.fields["permissions"].queryset = Permission.objects.filter(
                organization=organization
            )
            self.fields["inherits"].queryset = Role.objects.filter(organization=organization)
            self.fields["conflicts"].queryset = Role.objects.filter(organization=organization)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class RoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = RoleAssignment
        fields = ["user", "role", "team", "source", "justification", "expires_at"]
        widgets = {"expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, organization=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model

        if organization:
            self.fields["user"].queryset = get_user_model().objects.filter(
                organization=organization
            )
            self.fields["role"].queryset = Role.objects.filter(organization=organization)
            from identities.models import Team

            self.fields["team"].queryset = Team.objects.filter(organization=organization)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class AccessReviewForm(forms.ModelForm):
    class Meta:
        model = AccessReview
        fields = ["user", "status", "due_date", "notes"]
        widgets = {"due_date": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, organization=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model

        if organization:
            self.fields["user"].queryset = get_user_model().objects.filter(
                organization=organization
            )
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class AccessEventImportForm(forms.Form):
    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs["class"] = "form-control"
