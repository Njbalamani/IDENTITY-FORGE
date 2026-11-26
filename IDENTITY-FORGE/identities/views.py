from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from audit.services import log_action
from config.ui import active_organization
from identities.forms import IdentityProfileForm, TeamForm
from identities.models import IdentityProfile, Team


@login_required
def team_list(request):
    organization = active_organization(request)
    teams = Team.objects.filter(organization=organization) if organization else Team.objects.none()
    return render(
        request, "identities/team_list.html", {"teams": teams, "organization": organization}
    )


@login_required
def team_create(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to manage teams.")
        return redirect("teams")
    organization = active_organization(request)
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("teams")
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.organization = organization
            team.save()
            log_action(
                organization,
                request.user,
                "Created team",
                "Team",
                team.id,
                {"name": team.name},
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, f"Created team {team.name}.")
            return redirect("teams")
    else:
        form = TeamForm()
    return render(request, "identities/team_form.html", {"form": form, "title": "Create team"})


@login_required
def profile_list(request):
    organization = active_organization(request)
    profiles = (
        IdentityProfile.objects.filter(organization=organization).select_related("user", "team")
        if organization
        else IdentityProfile.objects.none()
    )
    return render(
        request,
        "identities/profile_list.html",
        {"profiles": profiles, "organization": organization},
    )


@login_required
def profile_update(request, pk):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to edit profiles.")
        return redirect("profiles")
    organization = active_organization(request)
    profile = get_object_or_404(IdentityProfile, id=pk, organization=organization)
    if request.method == "POST":
        form = IdentityProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            log_action(
                organization,
                request.user,
                "Updated identity profile",
                "IdentityProfile",
                profile.id,
                {"username": profile.user.username},
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, "Identity profile updated.")
            return redirect("profiles")
    else:
        form = IdentityProfileForm(instance=profile)
    return render(request, "identities/profile_form.html", {"form": form, "profile": profile})
