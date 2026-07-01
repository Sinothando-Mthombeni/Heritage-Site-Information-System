"""
heritage_backend/core/management/commands/load_seed.py

Idempotent seed loader: loads seed_data.json (or seed_data_enriched.json
if it exists) into the database without duplicating records on repeated runs.

Usage:
    python manage.py load_seed                # loads seed_data.json
    python manage.py load_seed --enriched     # loads seed_data_enriched.json
    python manage.py load_seed --flush        # clears all site data first
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from heritage_backend.core.models import Category, HeritageSite, Province


class Command(BaseCommand):
    help = "Load curated heritage site seed data into the database (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--enriched",
            action="store_true",
            help="Use seed_data_enriched.json (Wikidata-enriched) if available.",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing Province/Category/HeritageSite records first. "
                 "WARNING: this will also delete all Bookings and Visitors via CASCADE.",
        )

    def handle(self, *args, **options):
        fixture_dir = (
            Path(__file__).resolve().parent.parent.parent / "fixtures"
        )

        if options["enriched"]:
            path = fixture_dir / "seed_data_enriched.json"
            if not path.exists():
                raise CommandError(
                    "seed_data_enriched.json not found. "
                    "Run scripts/enrich_from_wikidata.py first."
                )
        else:
            path = fixture_dir / "seed_data.json"
            if not path.exists():
                raise CommandError(f"Fixture not found: {path}")

        self.stdout.write(f"Loading seed data from {path.name}...")

        with open(path, encoding="utf-8") as f:
            records = json.load(f)

        if options["flush"]:
            self.stdout.write(self.style.WARNING("  Flushing existing data..."))
            with transaction.atomic():
                HeritageSite.objects.all().delete()
                Category.objects.all().delete()
                Province.objects.all().delete()

        with transaction.atomic():
            self._load_provinces(records)
            self._load_categories(records)
            self._load_sites(records)

        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully."))

    def _load_provinces(self, records):
        rows = [r for r in records if r["model"] == "core.province"]
        created = updated = 0
        for row in rows:
            obj, was_created = Province.objects.update_or_create(
                province_id=row["pk"],
                defaults={"name": row["fields"]["name"]},
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(f"  Provinces — {created} created, {updated} already existed.")

    def _load_categories(self, records):
        rows = [r for r in records if r["model"] == "core.category"]
        created = updated = 0
        for row in rows:
            obj, was_created = Category.objects.update_or_create(
                category_id=row["pk"],
                defaults={"name": row["fields"]["name"]},
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(f"  Categories — {created} created, {updated} already existed.")

    def _load_sites(self, records):
        rows = [r for r in records if r["model"] == "core.heritagesite"]
        created = updated = 0
        for row in rows:
            fields = row["fields"]
            try:
                province = Province.objects.get(pk=fields["province"])
                category = Category.objects.get(pk=fields["category"])
            except (Province.DoesNotExist, Category.DoesNotExist) as e:
                self.stderr.write(
                    f"  Skipping site '{fields['name']}': {e}"
                )
                continue

            # Only the fields defined on the model (ignore any Wikidata extras
            # like latitude/longitude/image_url that aren't on the model yet)
            site_defaults = {
                "description": fields["description"],
                "entry_fee":   fields.get("entry_fee"),
                "is_active":   fields.get("is_active", True),
                "province":    province,
                "category":    category,
            }

            obj, was_created = HeritageSite.objects.update_or_create(
                site_id=row["pk"],
                defaults=site_defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(f"  Heritage sites — {created} created, {updated} already existed.")
