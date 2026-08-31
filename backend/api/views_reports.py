"""
api/views_reports.py

PostgreSQL-backed reporting endpoints. Each view delegates to a
service function and handles serialisation edge cases:
  - Decimal (entry_fee) → DjangoJSONEncoder
  - average_group_size() returns a dict aggregate → extract the value
  - monthly_booking_stats() returns raw SQL tuples → convert to dicts
"""
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
import random
from heritage_backend.core.models import HeritageSite


from heritage_backend.services.reporting_service import (
    average_group_size,
    bookings_per_site,
    monthly_booking_stats,
    sites_with_provinces,
)


def bookings_per_site_view(request):
    """GET /api/reports/bookings-per-site/
    Returns a list of {heritage_site__name, total} ordered by most bookings.
    """
    data = list(bookings_per_site())
    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)


def average_group_size_view(request):
    """GET /api/reports/average-group-size/
    Returns {"average_group_size": <float>} across all bookings.
    average_group_size() returns Django's Avg aggregate dict,
    e.g. {"avg_people": Decimal("2.50")} or {"avg_people": None}.
    """
    result = average_group_size()
    raw = result.get("avg_people")
    value = round(float(raw), 2) if raw is not None else 0
    return JsonResponse({"average_group_size": value})


def monthly_booking_stats_view(request):
    """GET /api/reports/monthly-stats/
    Returns a list of {month, total_bookings} per calendar month.
    monthly_booking_stats() executes raw SQL and returns a list of
    tuples: [(datetime, int), ...] — these must be converted to dicts.
    """
    rows = monthly_booking_stats()
    data = [
        {"month": str(row[0])[:7], "total_bookings": row[1]}   # "YYYY-MM"
        for row in rows
    ]
    return JsonResponse(data, safe=False)


def sites_with_provinces_view(request):
    """GET /api/reports/sites/
    Returns all active heritage sites with their province name.
    Uses DjangoJSONEncoder to handle Decimal entry_fee values.
    """
    qs = sites_with_provinces().values(
        "site_id", "name", "province__name", "entry_fee", "is_active"
    )
    return JsonResponse(list(qs), safe=False, encoder=DjangoJSONEncoder)

# ── Phase 1: public-safe aggregations ────────────────────────────────────

def sites_by_province_count(request):
    from django.db.models import Count
    data = list(HeritageSite.objects.filter(is_active=True).values('province__name').annotate(count=Count('site_id')).order_by('province__name'))
    return JsonResponse(data, safe=False)

def sites_by_category_count(request):
    from django.db.models import Count
    data = list(HeritageSite.objects.filter(is_active=True).values('category__name').annotate(count=Count('site_id')).order_by('category__name'))
    return JsonResponse(data, safe=False)

def featured_sites_view(request):
    all_ids = list(HeritageSite.objects.filter(is_active=True).values_list('site_id',flat=True))
    selected = random.sample(all_ids, min(3, len(all_ids)))
    sites = HeritageSite.objects.filter(site_id__in=selected).select_related('province','category')
    return JsonResponse([{'site_id':s.site_id,'name':s.name,'description':s.description,'province':s.province.name,'category':s.category.name,'entry_fee':float(s.entry_fee) if s.entry_fee else None} for s in sites], safe=False)

# ── Phase 2: completeness additions ──────────────────────────────────────
def site_detail_view(request, site_id):
    try:
        s = HeritageSite.objects.select_related('province','category').get(pk=site_id, is_active=True)
        return JsonResponse({'site_id':s.site_id,'name':s.name,'description':s.description,'entry_fee':float(s.entry_fee) if s.entry_fee else None,'province':s.province.name,'category':s.category.name})
    except HeritageSite.DoesNotExist:
        return JsonResponse({'status':'error','message':'Site not found'},status=404)

def export_bookings_csv(request):
    import csv
    from django.http import StreamingHttpResponse
    from heritage_backend.core.models import Booking
    def rows():
        yield ['booking_id','visitor_name','visitor_email','site_name','visit_date','number_of_people','booking_date','is_cancelled']
        for bk in Booking.objects.select_related('visitor','heritage_site').all():
            yield [bk.booking_id,bk.visitor.full_name,bk.visitor.email,bk.heritage_site.name,bk.visit_date,bk.number_of_people,bk.booking_date,bk.is_cancelled]
    class Echo:
        def write(self, v): return v
    w = csv.writer(Echo())
    resp = StreamingHttpResponse((w.writerow(r) for r in rows()), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename=bookings.csv'
    return resp

