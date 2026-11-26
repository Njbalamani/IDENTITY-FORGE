from django.urls import path

from reports.views import report_generate, report_list

urlpatterns = [
    path("", report_list, name="reports"),
    path("generate/", report_generate, name="report-generate"),
]
