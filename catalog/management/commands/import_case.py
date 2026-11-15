from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.importer import import_case
from catalog.loader import CaseError, case_folders


class Command(BaseCommand):
    help = "Check case folders and load them into the case list."

    def add_arguments(self, parser):
        parser.add_argument("folders", nargs="*", help="Case folders, or slugs inside CASES_DIR. Default: every case.")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--publish", action="store_true", help="Show the case in the case browser")
        group.add_argument("--draft", action="store_true", help="Hide the case from the case browser")

    def handle(self, *args, folders, publish, draft, **options):
        published = True if publish else False if draft else None
        paths = [self._resolve(f) for f in folders] or case_folders()
        if not paths:
            raise CommandError(f"No case folders found in {settings.CASES_DIR}")

        failed = 0
        for path in paths:
            try:
                case = import_case(path, published=published)
            except CaseError as e:
                failed += 1
                self.stderr.write(self.style.ERROR(f"{path.name}: {len(e.problems)} problem(s)"))
                for problem in e.problems:
                    self.stderr.write(f"  - {problem}")
                continue
            state = "published" if case.published else "draft"
            self.stdout.write(self.style.SUCCESS(
                f"{case.slug}: {case.title} ({state}; {case.min_players}-{case.max_players} players, "
                f"{case.clue_count} clues, {case.puzzle_count} puzzles, {case.prop_count} props)"
            ))
        if failed:
            raise CommandError(f"{failed} case(s) not imported")

    def _resolve(self, value):
        path = Path(value)
        if not path.is_dir():
            path = settings.CASES_DIR / value
        if not (path / "case.json").is_file():
            raise CommandError(f"{value}: no case.json found")
        return path
