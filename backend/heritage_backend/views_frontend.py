"""
heritage_backend/views_frontend.py

Django template views for the frontend UI. These call the service layer
directly (no HTTP round-trip to the REST API) and render HTML templates.
"""
from django.shortcuts import render

from heritage_backend.services.reporting_service import sites_with_provinces


def home_view(request):
    """
    / — Home page.
    Lists all heritage sites with search/filter controls.
    """
    sites = list(
        sites_with_provinces()
        .values(
            "site_id", "name", "description",
            "entry_fee", "is_active",
            "province__name", "category__name",
        )
        .filter(is_active=True)
        .order_by("province__name", "name")
    )
    provinces  = sorted({s["province__name"] for s in sites})
    categories = sorted({s["category__name"]  for s in sites})

    return render(request, "heritage_backend/home.html", {
        "sites":       sites,
        "provinces":   provinces,
        "categories":  categories,
        "total_sites": len(sites),
    })


def dashboard_view(request):
    """
    /dashboard/ — Analytics dashboard.
    Charts and tables are populated client-side via JavaScript fetch
    calls to the /api/reports/* endpoints.
    """
    return render(request, "heritage_backend/dashboard.html")
