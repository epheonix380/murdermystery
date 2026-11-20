import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.mapsvg import render


class Command(BaseCommand):
    help = "Draw a case's floor plan from extras.json into public/map.svg. Run import_case afterwards to check the case."

    def add_arguments(self, parser):
        parser.add_argument("case", help="A case folder, or a slug inside CASES_DIR")

    def handle(self, *args, case, **options):
        folder = Path(case) if Path(case).is_dir() else settings.CASES_DIR / case
        try:
            manifest = json.loads((folder / "case.json").read_text())
            extras = json.loads((folder / manifest["files"]["extras"]).read_text())
            rooms = extras["map"]["rooms"]
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise CommandError(f"Need case.json, and an extras file with a map of rooms ({e!r})")
        if not rooms:
            raise CommandError("The map has no rooms")
        target = folder / "public" / "map.svg"
        target.parent.mkdir(exist_ok=True)
        target.write_text(render(extras["map"], f"Floor plan of {manifest.get('title', 'the case')}"))
        self.stdout.write(self.style.SUCCESS(f"wrote {target}"))
