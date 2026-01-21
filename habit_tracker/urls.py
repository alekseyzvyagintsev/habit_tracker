from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.reverse import reverse

from habit_tracker import settings


@login_required(login_url="/admin/login/")
def redirect_to_swagger(request):
    return HttpResponseRedirect(reverse("swagger-ui"))

urlpatterns = [
    path('admin/', admin.site.urls),
    path("admindocs/", include("django.contrib.admindocs.urls")),
    path("", include("users.urls", namespace="users_urls")),
    # Маршруты для схемы и документации
    re_path(r"^api/schema(?P<format>\.json|\.yaml)?$", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
