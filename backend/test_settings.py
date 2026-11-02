"""Settings for tests using disposable local PostgreSQL and MongoDB services."""
import os
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured


forbidden_database_urls = (
    "DATABASE_URL",
    "NEON_DATABASE_URL",
    "NEON_DATABASE_URL_UNPOOLED",
    "RESTORE_DATABASE_URL",
)
if any(os.environ.get(name) for name in forbidden_database_urls):
    raise ImproperlyConfigured(
        "Test settings reject inherited database URL variables."
    )

database_name = os.environ.get(
    "HERITAGE_TEST_DB_NAME", "heritage_phase2_test"
)
if database_name != "heritage_phase2_test":
    raise ImproperlyConfigured(
        "Test settings require the dedicated heritage_phase2_test database."
    )

database_host = os.environ.get("HERITAGE_TEST_DB_HOST", "127.0.0.1")
if database_host not in {"localhost", "127.0.0.1", "::1"}:
    raise ImproperlyConfigured(
        "Test settings permit only an isolated local PostgreSQL service."
    )

mongo_database_name = os.environ.get(
    "HERITAGE_TEST_MONGO_DB_NAME", "heritage_phase2_test"
)
if mongo_database_name != "heritage_phase2_test":
    raise ImproperlyConfigured(
        "Test settings require the dedicated heritage_phase2_test Mongo database."
    )

mongo_uri = os.environ.get(
    "HERITAGE_TEST_MONGO_URI", "mongodb://127.0.0.1:27018/"
)
mongo_host = urlparse(mongo_uri).hostname
if mongo_host not in {"localhost", "127.0.0.1", "::1"}:
    raise ImproperlyConfigured(
        "Test settings permit only an isolated local MongoDB service."
    )

os.environ.update({
    "SECRET_KEY": "phase2-test-only-secret-key",
    "DEBUG": "True",
    "DB_NAME": database_name,
    "DB_USER": os.environ.get("HERITAGE_TEST_DB_USER", "heritage_test"),
    "DB_PASSWORD": os.environ.get(
        "HERITAGE_TEST_DB_PASSWORD", "heritage_test_only"
    ),
    "DB_HOST": database_host,
    "DB_PORT": os.environ.get("HERITAGE_TEST_DB_PORT", "55432"),
    "DB_SSLMODE": "disable",
    "MONGO_URI": mongo_uri,
    "MONGO_DB_NAME": mongo_database_name,
    "SENTRY_DSN": "",
})

from settings import *  # noqa: E402,F403

if any(os.environ.get(name) for name in forbidden_database_urls):
    raise ImproperlyConfigured(
        "Test settings reject database URL variables loaded from dotenv."
    )

DATABASES["default"]["NAME"] = database_name
DATABASES["default"]["USER"] = os.environ["DB_USER"]
DATABASES["default"]["PASSWORD"] = os.environ["DB_PASSWORD"]
DATABASES["default"]["HOST"] = os.environ["DB_HOST"]
DATABASES["default"]["PORT"] = os.environ["DB_PORT"]
DATABASES["default"]["OPTIONS"] = {"sslmode": "disable"}
MONGO_URI = mongo_uri
MONGO_DB_NAME = mongo_database_name
