from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, ChatMessageViewSet,
)

router = DefaultRouter()
router.register(r"messages", ChatMessageViewSet, basename="messages")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/",    LoginView.as_view(),    name="token_obtain_pair"),
    path("", include(router.urls)),
]