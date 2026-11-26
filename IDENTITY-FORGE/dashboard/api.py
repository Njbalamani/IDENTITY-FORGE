from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.metrics import dashboard_metrics


class DashboardMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(dashboard_metrics(request.user.organization))
