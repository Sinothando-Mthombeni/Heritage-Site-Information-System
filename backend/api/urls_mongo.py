from django.urls import path
from .views_mongo import *

urlpatterns = [
    path("mongo/sites/", all_heritage_sites),
    path("mongo/sites/province/<str:province>/", heritage_sites_by_province),
    path("mongo/sites/<str:name>/", heritage_site_detail),
    path("mongo/analytics/sites-per-province/", analytics_sites_per_province),
    path("mongo/analytics/average-fee/", analytics_average_fee),
]
