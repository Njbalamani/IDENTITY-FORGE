from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import RegisterSerializer, UserCreateSerializer, UserSerializer
from audit.services import log_action
from config.permissions import IsPlatformAdmin
from config.viewsets import OrganizationScopedViewSet


class UserViewSet(OrganizationScopedViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UserSerializer(request.user).data)


class RegisterAPIView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        log_action(
            user.organization,
            user,
            "Registered account",
            "User",
            user.id,
            {"username": user.username},
            self.request.META.get("REMOTE_ADDR"),
        )


class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
