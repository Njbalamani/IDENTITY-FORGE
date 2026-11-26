from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from certification.forms import CampaignForm
from certification.models import Campaign, CampaignItem
from certification.services import apply_decisions, create_campaign, decide_item
from config.ui import active_organization


def can_manage(user):
    return user.is_platform_admin or user.platform_role == user.PlatformRole.SECURITY_ANALYST


@login_required
def campaign_list(request):
    organization = active_organization(request)
    campaigns = (
        Campaign.objects.filter(organization=organization).prefetch_related("items", "reviewers")
        if organization
        else Campaign.objects.none()
    )
    return render(
        request,
        "certification/list.html",
        {
            "campaigns": campaigns,
            "organization": organization,
            "can_manage": can_manage(request.user),
        },
    )


@login_required
def campaign_create(request):
    organization = active_organization(request)
    if not can_manage(request.user):
        messages.error(request, "Security analyst access is required to create campaigns.")
        return redirect("campaigns")
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("campaigns")
    if request.method == "POST":
        form = CampaignForm(organization, request.POST)
        if form.is_valid():
            campaign = create_campaign(
                organization,
                request.user,
                form.cleaned_data["name"],
                form.cleaned_data["due_date"],
                form.cleaned_data["reviewers"],
                request.META.get("REMOTE_ADDR"),
            )
            messages.success(request, f"Created certification campaign {campaign.name}.")
            return redirect("campaign-detail", pk=campaign.pk)
    else:
        form = CampaignForm(organization)
    return render(
        request,
        "certification/form.html",
        {"form": form, "title": "Create certification campaign"},
    )


@login_required
def campaign_detail(request, pk):
    organization = active_organization(request)
    campaign = get_object_or_404(Campaign, pk=pk, organization=organization)
    items = campaign.items.select_related("user", "role", "assignment").order_by(
        "user__username", "role__name"
    )
    can_decide = (
        request.user.is_platform_admin or campaign.reviewers.filter(id=request.user.id).exists()
    )
    return render(
        request,
        "certification/detail.html",
        {
            "campaign": campaign,
            "items": items,
            "organization": organization,
            "can_decide": can_decide,
            "can_manage": can_manage(request.user),
        },
    )


@login_required
@require_POST
def campaign_item_decide(request, pk):
    organization = active_organization(request)
    item = get_object_or_404(CampaignItem, pk=pk, campaign__organization=organization)
    if (
        not request.user.is_platform_admin
        and not item.campaign.reviewers.filter(id=request.user.id).exists()
    ):
        messages.error(request, "You are not assigned to this certification campaign.")
        return redirect("campaign-detail", pk=item.campaign_id)
    try:
        decide_item(
            item,
            request.user,
            request.POST.get("decision"),
            request.POST.get("note", ""),
            request.META.get("REMOTE_ADDR"),
        )
        messages.success(request, "Certification decision recorded.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("campaign-detail", pk=item.campaign_id)


@login_required
@require_POST
def campaign_apply(request, pk):
    organization = active_organization(request)
    campaign = get_object_or_404(Campaign, pk=pk, organization=organization)
    if not can_manage(request.user):
        messages.error(request, "Security analyst access is required to apply decisions.")
        return redirect("campaign-detail", pk=campaign.pk)
    try:
        revoked = apply_decisions(campaign, request.user, request.META.get("REMOTE_ADDR"))
        messages.success(request, f"Certification applied. {revoked} assignment(s) revoked.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("campaign-detail", pk=campaign.pk)
