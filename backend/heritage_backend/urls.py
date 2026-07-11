from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls_mongo")),
    path("api/", include("api.urls_pg")),
    path("api/", include("api.urls_reports")),
]
