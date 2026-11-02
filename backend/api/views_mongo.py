from django.http import JsonResponse
from django.views.decorators.http import require_GET
from api.decorators import api_error_handler
from mongo.heritage_sites import (
    get_all_sites,
    get_sites_by_province,
    get_site_by_name
)
from mongo.analytics import (
    sites_per_province,
    average_entry_fee
)


PAGE_SIZE_DEFAULT = 10
PAGE_SIZE_MAX = 100


def _positive_query_int(request, name, default, maximum=None):
    value = request.GET.get(name)
    if value is None:
        return default, None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, JsonResponse(
            {"status": "error", "errors": {name: ["Enter a positive integer."]}},
            status=400,
        )
    if parsed < 1 or (maximum is not None and parsed > maximum):
        message = (
            f"Ensure this value is between 1 and {maximum}."
            if maximum is not None
            else "Enter a positive integer."
        )
        return None, JsonResponse(
            {"status": "error", "errors": {name: [message]}},
            status=400,
        )
    return parsed, None


@api_error_handler
@require_GET
def all_heritage_sites(request):
    page, error = _positive_query_int(request, "page", 1)
    if error:
        return error
    page_size, error = _positive_query_int(
        request, "page_size", PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX
    )
    if error:
        return error
    if (page - 1) * page_size > (2**63) - 1:
        return JsonResponse(
            {"status": "error", "errors": {"page": ["Page number is too large."]}},
            status=400,
        )
    return JsonResponse(get_all_sites(page, page_size), safe=False)


@api_error_handler
@require_GET
def heritage_sites_by_province(request, province):
    return JsonResponse(get_sites_by_province(province), safe=False)


@api_error_handler
@require_GET
def heritage_site_detail(request, name):
    site = get_site_by_name(name)
    if site is None:
        return JsonResponse(
            {"status": "error", "message": "Site not found."},
            status=404,
        )
    return JsonResponse(site, safe=False)


@api_error_handler
@require_GET
def analytics_sites_per_province(request):
    return JsonResponse(sites_per_province(), safe=False)


@api_error_handler
@require_GET
def analytics_average_fee(request):
    return JsonResponse({"average_fee": average_entry_fee()})
