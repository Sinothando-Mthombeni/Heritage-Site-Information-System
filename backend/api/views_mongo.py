from django.http import JsonResponse
from mongo.heritage_sites import (
    get_all_sites,
    get_sites_by_province,
    get_site_by_name
)
from mongo.analytics import (
    sites_per_province,
    average_entry_fee
)

def all_heritage_sites(request):
    return JsonResponse(get_all_sites(), safe=False)

def heritage_sites_by_province(request, province):
    return JsonResponse(get_sites_by_province(province), safe=False)

def heritage_site_detail(request, name):
    site = get_site_by_name(name)
    return JsonResponse(site if site else {}, safe=False)

def analytics_sites_per_province(request):
    return JsonResponse(sites_per_province(), safe=False)

def analytics_average_fee(request):
    return JsonResponse({"average_fee": average_entry_fee()})
