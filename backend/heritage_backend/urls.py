from django.contrib import admin
from django.urls import path, include

from heritage_backend.views_frontend import home_view, dashboard_view

urlpatterns = [
    # Frontend pages
    path("",           home_view,      name="home"),
    path("dashboard/", dashboard_view, name="dashboard"),

    # Admin
    path("admin/", admin.site.urls),

    # REST API
    path("api/", include("api.urls_mongo")),
    path("api/", include("api.urls_pg")),
    path("api/", include("api.urls_reports")),
]
