from django.urls import path

from audit.views import audit_list

urlpatterns = [path("", audit_list, name="audit")]
