from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import UserCreateForm, UserUpdateForm
from audit.services import log_action
from config.ui import active_organization


class IdentityForgeLoginView(LoginView):
    authentication_form = AuthenticationForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def user_list(request):
    organization = active_organization(request)
    if organization:
        users = get_user_model().objects.filter(organization=organization)
    elif request.user.is_platform_admin:
        users = get_user_model().objects.all()
    else:
        users = get_user_model().objects.filter(id=request.user.id)
    return render(
        request, "accounts/user_list.html", {"users": users, "organization": organization}
    )


@login_required
def user_create(request):
    if not request.user.is_platform_admin:
        messages.error(request, "Administrator access is required to create identities.")
        return redirect("users")
    organization = active_organization(request)
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(
                user.organization,
                request.user,
                "Created identity",
                "User",
                user.id,
                {"username": user.username},
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, f"Created identity {user.username}.")
            return redirect("users")
    else:
        form = UserCreateForm(initial={"organization": organization})
    return render(request, "accounts/user_form.html", {"form": form, "title": "Create identity"})


@login_required
def user_update(request, pk):
    organization = active_organization(request)
    if not request.user.is_platform_admin:
        messages.error(request, "Administrator access is required to edit identities.")
        return redirect("users")
    user = get_object_or_404(get_user_model(), id=pk, organization=organization)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_action(
                organization,
                request.user,
                "Updated identity",
                "User",
                user.id,
                {"username": user.username},
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, f"Updated identity {user.username}.")
            return redirect("users")
    else:
        form = UserUpdateForm(instance=user)
    return render(
        request, "accounts/user_form.html", {"form": form, "title": "Edit identity", "target": user}
    )
