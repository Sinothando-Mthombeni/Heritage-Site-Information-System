from django.urls import path
from .views_pg import create_booking_view, cancel_booking_view

urlpatterns = [
    path('bookings/create/',               create_booking_view),
    path('bookings/<int:booking_id>/cancel/', cancel_booking_view),
    # Phase 3: auth endpoints moved to heritage_backend/urls_auth.py
]

