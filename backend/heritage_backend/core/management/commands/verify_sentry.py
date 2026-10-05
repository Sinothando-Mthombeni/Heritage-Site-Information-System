import sentry_sdk

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send a controlled test event to Sentry."

    def handle(self, *args, **options):
        self.stdout.write("Checking Sentry initialization...")

        if not sentry_sdk.is_initialized():
            self.stderr.write(
                self.style.ERROR(
                    "Sentry is not initialized. Check SENTRY_DSN and configuration."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS("Sentry is initialized.")
        )

        try:
            raise RuntimeError(
                "HeritageSA infrastructure verification test"
            )
        except RuntimeError:
            event_id = sentry_sdk.capture_exception()

        sentry_sdk.flush(timeout=10)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sentry test event sent. Event ID: {event_id}"
            )
        )