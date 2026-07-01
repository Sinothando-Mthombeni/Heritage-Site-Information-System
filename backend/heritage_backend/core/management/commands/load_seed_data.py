"""
Loads the curated static heritage site dataset (data/heritage_sites_seed.json)
into PostgreSQL via the Django ORM.

This is the PRIMARY data path for the project: a hand-researched, offline,
demo-safe dataset. See scripts/enrich_from_wikidata.py for the optional,
secondary enrichment path that pulls supplementary fields from Wikidata.

Usage:
    python manage.py load_seed_data
    python manage.py load_seed_data --file path/to/other_seed.json
    python manage.py load_seed_data --clear   # wipe existing sites/provinces/categories first
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from heritage_backend.core.models import Category, HeritageSite, Province

DEFAULT_SEED_PATH = Path(__file__).resolve().parents[4] / "data" / "heritage_sites_seed.json"


class Command(BaseCommand):
    help = "Load the curated heritage site dataset into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=str(DEFAULT_SEED_PATH),
            help="Path to the seed JSON file (default: data/heritage_sites_seed.json)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing HeritageSite/Province/Category rows before loading.",
        )

    def handle(self, *args, **options):
        seed_path = Path(options["file"])
        if not seed_path.exists():
            self.stderr.write(self.style.ERROR(f"Seed file not found: {seed_path}"))
            return

        data = json.loads(seed_path.read_text(encoding="utf-8"))
        sites = data.get("sites", [])

        if not sites:
            self.stderr.write(self.style.ERROR("Seed file contains no sites."))
            return

        with transaction.atomic():
            if options["clear"]:
                HeritageSite.objects.all().delete()
                Province.objects.all().delete()
                Category.objects.all().delete()
                self.stdout.write(self.style.WARNING("Cleared existing sites/provinces/categories."))

            province_cache = {}
            category_cache = {}
            created, updated = 0, 0

            for entry in sites:
                province_name = entry["province"]
                category_name = entry["category"]

                if province_name not in province_cache:
                    province_cache[province_name], _ = Province.objects.get_or_create(name=province_name)
                if category_name not in category_cache:
                    category_cache[category_name], _ = Category.objects.get_or_create(name=category_name)

                obj, was_created = HeritageSite.objects.update_or_create(
                    name=entry["name"],
                    defaults={
                        "description": entry.get("description", ""),
                        "entry_fee": entry.get("entry_fee"),
                        "is_active": entry.get("is_active", True),
                        "province": province_cache[province_name],
                        "category": category_cache[category_name],
                    },
                )
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Seed load complete: {created} site(s) created, {updated} site(s) updated, "
            f"{len(province_cache)} province(s), {len(category_cache)} category(ies)."
        ))
