from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "display_name", "platform_role", "organization"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "display_name", "platform_role", "organization", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
