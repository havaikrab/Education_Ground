from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import settings

urlpatterns: list = [
    path("admin/", admin.site.urls),
    path("", include("education.urls", namespace="education")),
    path("users/", include("users.urls", namespace="users")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
