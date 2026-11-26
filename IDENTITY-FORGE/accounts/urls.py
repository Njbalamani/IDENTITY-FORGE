from django.urls import path

from accounts.views import IdentityForgeLoginView, logout_view, user_create, user_list, user_update

urlpatterns = [
    path("login/", IdentityForgeLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("", user_list, name="users"),
    path("create/", user_create, name="user-create"),
    path("<int:pk>/edit/", user_update, name="user-update"),
]
