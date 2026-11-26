from django.urls import path

from access.views import (
    assignment_create,
    assignment_list,
    event_import,
    event_list,
    permission_create,
    permission_list,
    review_complete,
    review_create,
    review_list,
    role_create,
    role_list,
)

urlpatterns = [
    path("roles/", role_list, name="roles"),
    path("roles/create/", role_create, name="role-create"),
    path("permissions/", permission_list, name="permissions"),
    path("permissions/create/", permission_create, name="permission-create"),
    path("assignments/", assignment_list, name="assignments"),
    path("assignments/create/", assignment_create, name="assignment-create"),
    path("events/", event_list, name="events"),
    path("events/import/", event_import, name="event-import"),
    path("reviews/", review_list, name="reviews"),
    path("reviews/create/", review_create, name="review-create"),
    path("reviews/<int:pk>/complete/", review_complete, name="review-complete"),
]
