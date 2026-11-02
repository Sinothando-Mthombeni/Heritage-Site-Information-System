import logging
from functools import wraps

from django.db import DatabaseError
from django.http import JsonResponse
from pymongo.errors import PyMongoError


logger = logging.getLogger("heritage_backend")


def api_error_handler(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except (DatabaseError, PyMongoError) as error:
            logger.error(
                "API data service failed in %s (%s)",
                view_func.__name__,
                type(error).__name__,
            )
            return JsonResponse(
                {
                    "status": "error",
                    "message": "A required data service is temporarily unavailable.",
                },
                status=503,
            )
        except Exception as error:
            logger.error(
                "Unhandled API error in %s (%s)",
                view_func.__name__,
                type(error).__name__,
            )
            return JsonResponse(
                {"status": "error", "message": "An unexpected server error occurred."},
                status=500,
            )

    return wrapper
