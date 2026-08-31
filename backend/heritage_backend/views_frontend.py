from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from heritage_backend.services.reporting_service import sites_with_provinces


def home_view(request):
    sites = list(sites_with_provinces().values(
        'site_id','name','description','entry_fee','is_active','province__name','category__name'
).filter(is_active=True).order_by('province__name','name'))
    provinces  = sorted({s['province__name'] for s in sites})
    categories = sorted({s['category__name']  for s in sites})
    return render(request,'heritage_backend/home.html',{
        'sites':sites,'provinces':provinces,'categories':categories,'total_sites':len(sites)})


def discover_view(request):
    from heritage_backend.core.models import HeritageSite,Province,Category
    return render(request,'heritage_backend/discover.html',{
        'total_sites':HeritageSite.objects.filter(is_active=True).count(),
        'total_provinces':Province.objects.count(),
        'total_categories':Category.objects.count()})


@staff_member_required
def admin_dashboard_view(request):
    return render(request,'heritage_backend/admin_dashboard.html')
