#############################################################################################################
from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from users.apps import UsersConfig
from users.views import UserCreateAPIView, UserViewSet

app_name = UsersConfig.name

# Регистрируем ViewSets для модели User
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")  # Роутер для пользователя


urlpatterns = [
    path("register/", UserCreateAPIView.as_view(permission_classes=(AllowAny,)), name="user-create"),
    path("login/", TokenObtainPairView.as_view(permission_classes=(AllowAny,)), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(permission_classes=(AllowAny,)), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]

urlpatterns += router.urls  # Включаем автоматически созданные URL-адреса


#############################################################################################################
