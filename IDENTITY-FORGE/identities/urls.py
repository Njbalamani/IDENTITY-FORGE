from django.urls import path

from identities.views import profile_list, profile_update, team_create, team_list

urlpatterns = [
    path("teams/", team_list, name="teams"),
    path("teams/create/", team_create, name="team-create"),
    path("profiles/", profile_list, name="profiles"),
    path("profiles/<int:pk>/edit/", profile_update, name="profile-update"),
]
