from django.urls import path

from certification.views import (
    campaign_apply,
    campaign_create,
    campaign_detail,
    campaign_item_decide,
    campaign_list,
)

urlpatterns = [
    path("", campaign_list, name="campaigns"),
    path("create/", campaign_create, name="campaign-create"),
    path("<int:pk>/", campaign_detail, name="campaign-detail"),
    path("<int:pk>/apply/", campaign_apply, name="campaign-apply"),
    path("items/<int:pk>/decide/", campaign_item_decide, name="campaign-item-decide"),
]
