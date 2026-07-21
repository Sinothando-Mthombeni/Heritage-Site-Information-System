"""
api/serializers.py

DRF serializer for booking creation. Provides field-level validation
with clear per-field error messages rather than a bare try/except.
"""
from datetime import date

from rest_framework import serializers


class BookingSerializer(serializers.Serializer):
    visitor_email    = serializers.EmailField()
    visitor_name     = serializers.CharField(max_length=255, min_length=1)
    site_id          = serializers.IntegerField(min_value=1)
    visit_date       = serializers.DateField()
    number_of_people = serializers.IntegerField(min_value=1)

    def validate_visit_date(self, value):
        """Reject dates that are strictly in the past."""
        if value < date.today():
            raise serializers.ValidationError(
                "Visit date cannot be in the past."
            )
        return value

    def validate_visitor_name(self, value):
        """Reject names that are only whitespace."""
        if not value.strip():
            raise serializers.ValidationError(
                "Visitor name cannot be blank."
            )
        return value.strip()
