from django.urls import path
from .views_pg import create_booking_view

urlpatterns = [
    path("bookings/create/", create_booking_view),
]
