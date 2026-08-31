from django.contrib import admin
from django.urls import path, include
from heritage_backend.views_frontend import home_view, discover_view, admin_dashboard_view

urlpatterns = [
    path('',               home_view,            name='home'),
    path('discover/',      discover_view,        name='discover'),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls_mongo')),
    path('api/', include('api.urls_pg')),
    path('api/', include('api.urls_reports')),
    # Phase 3: path('', include('heritage_backend.urls_auth')),
]
