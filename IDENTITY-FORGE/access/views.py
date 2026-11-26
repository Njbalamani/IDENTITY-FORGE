from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from access.forms import (
    AccessEventImportForm,
    AccessReviewForm,
    PermissionForm,
    RoleAssignmentForm,
    RoleForm,
)
from access.models import (
    AccessEvent,
    AccessReview,
    Permission,
    Role,
    RoleAssignment,
)
from analysis.imports import import_access_events
from audit.services import log_action
from config.ui import active_organization


@login_required
def role_list(request):
    organization = active_organization(request)
    roles = (
        Role.objects.filter(organization=organization).prefetch_related("permissions", "inherits")
        if organization
        else Role.objects.none()
    )
    return render(request, "access/role_list.html", {"roles": roles, "organization": organization})


@login_required
def role_create(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to manage roles.")
        return redirect("roles")
    organization = active_organization(request)
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("roles")
    if request.method == "POST":
        form = RoleForm(organization, request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.organization = organization
            role.save()
            form.save_m2m()
            log_action(
                organization,
                request.user,
                "Created role",
                "Role",
                role.id,
                {"name": role.name},
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, f"Created role {role.name}.")
            return redirect("roles")
    else:
        form = RoleForm(organization)
    return render(request, "access/role_form.html", {"form": form, "title": "Create role"})


@login_required
def permission_list(request):
    organization = active_organization(request)
    permissions = (
        Permission.objects.filter(organization=organization)
        if organization
        else Permission.objects.none()
    )
    return render(
        request,
        "access/permission_list.html",
        {"permissions": permissions, "organization": organization},
    )


@login_required
def permission_create(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to manage permissions.")
        return redirect("permissions")
    organization = active_organization(request)
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("permissions")
    if request.method == "POST":
        form = PermissionForm(request.POST)
        if form.is_valid():
            permission = form.save(commit=False)
            permission.organization = organization
            permission.save()
            messages.success(request, f"Created permission {permission.code}.")
            return redirect("permissions")
    else:
        form = PermissionForm()
    return render(
        request, "access/permission_form.html", {"form": form, "title": "Create permission"}
    )


@login_required
def assignment_list(request):
    organization = active_organization(request)
    assignments = (
        RoleAssignment.objects.filter(role__organization=organization).select_related(
            "user", "role", "team"
        )
        if organization
        else RoleAssignment.objects.none()
    )
    return render(
        request,
        "access/assignment_list.html",
        {"assignments": assignments, "organization": organization},
    )


@login_required
def assignment_create(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to assign roles.")
        return redirect("assignments")
    organization = active_organization(request)
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("assignments")
    if request.method == "POST":
        form = RoleAssignmentForm(organization, request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.granted_by = request.user
            assignment.save()
            log_action(
                organization,
                request.user,
                "Assigned role",
                "RoleAssignment",
                assignment.id,
                {"user": assignment.user.username, "role": assignment.role.name},
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, "Role assignment created.")
            return redirect("assignments")
    else:
        form = RoleAssignmentForm(organization)
    return render(request, "access/assignment_form.html", {"form": form, "title": "Assign role"})


@login_required
def event_list(request):
    organization = active_organization(request)
    events = (
        AccessEvent.objects.filter(organization=organization).select_related("user", "resource")
        if organization
        else AccessEvent.objects.none()
    )
    event_type = request.GET.get("event_type")
    if event_type:
        events = events.filter(event_type=event_type)
    return render(
        request,
        "access/event_list.html",
        {
            "events": events[:300],
            "event_types": AccessEvent.EventType.choices,
            "selected_type": event_type,
            "import_form": AccessEventImportForm(),
            "organization": organization,
        },
    )


@login_required
@require_POST
def event_import(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to import events.")
        return redirect("events")
    organization = active_organization(request)
    form = AccessEventImportForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            count = import_access_events(organization, form.cleaned_data["file"])
            messages.success(request, f"Imported {count} access events.")
            log_action(
                organization,
                request.user,
                "Imported access events",
                "AccessEvent",
                None,
                {"count": count},
                request.META.get("REMOTE_ADDR"),
            )
        except ValueError as exc:
            messages.error(request, str(exc))
    else:
        messages.error(request, "A valid CSV file is required.")
    return redirect("events")


@login_required
def review_list(request):
    organization = active_organization(request)
    reviews = (
        AccessReview.objects.filter(organization=organization).select_related("user", "reviewer")
        if organization
        else AccessReview.objects.none()
    )
    return render(
        request, "access/review_list.html", {"reviews": reviews, "organization": organization}
    )


@login_required
def review_create(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to create access reviews.")
        return redirect("reviews")
    organization = active_organization(request)
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("reviews")
    if request.method == "POST":
        form = AccessReviewForm(organization, request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.organization = organization
            review.save()
            messages.success(request, "Access review created.")
            return redirect("reviews")
    else:
        form = AccessReviewForm(organization)
    return render(
        request, "access/review_form.html", {"form": form, "title": "Create access review"}
    )


@login_required
@require_POST
def review_complete(request, pk):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required.")
        return redirect("reviews")
    organization = active_organization(request)
    review = get_object_or_404(AccessReview, id=pk, organization=organization)
    decision = request.POST.get("status")
    if decision not in {AccessReview.Status.APPROVED, AccessReview.Status.REJECTED}:
        messages.error(request, "Unsupported review decision.")
        return redirect("reviews")
    review.status = decision
    review.reviewer = request.user
    review.completed_at = timezone.now()
    review.notes = request.POST.get("notes", review.notes)
    review.save()
    log_action(
        organization,
        request.user,
        f"Completed access review {review.id}",
        "AccessReview",
        review.id,
        {"status": decision},
        request.META.get("REMOTE_ADDR"),
    )
    messages.success(request, "Access review completed.")
    return redirect("reviews")
