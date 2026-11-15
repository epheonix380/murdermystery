import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from catalog.models import Case


class ImportCommandTests(TestCase):
    def run_import(self, *args):
        out = StringIO()
        call_command("import_case", *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_imports_hollowpine(self):
        output = self.run_import("hollowpine")
        self.assertIn("44 clues, 3 puzzles, 2 props", output)
        case = Case.objects.get(slug="hollowpine")
        self.assertEqual(case.title, "The Last Chapter at Hollowpine Lodge")
        self.assertEqual((case.min_players, case.max_players), (4, 7))
        self.assertEqual((case.clue_count, case.puzzle_count, case.prop_count), (44, 3, 2))
        self.assertEqual(case.map_url, "/cases/hollowpine/public/map.svg")
        self.assertEqual(case.roles_file, "hollowpine/roles.json")
        self.assertEqual(case.extras_file, "hollowpine/extras.json")
        self.assertTrue(case.published)

    def test_reimport_updates_and_keeps_published(self):
        self.run_import("hollowpine", "--draft")
        self.run_import("hollowpine")
        self.assertEqual(Case.objects.count(), 1)
        self.assertFalse(Case.objects.get().published)
        self.run_import("hollowpine", "--publish")
        self.assertTrue(Case.objects.get().published)

    def test_imports_everything_by_default(self):
        self.run_import()
        self.assertTrue(Case.objects.filter(slug="hollowpine").exists())

    def test_unknown_folder(self):
        with self.assertRaisesMessage(CommandError, "no case.json found"):
            self.run_import("nope")


class BrokenImportTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(settings.CASES_DIR / "hollowpine", self.tmp / "hollowpine")
        roles = self.tmp / "hollowpine" / "roles.json"
        data = json.loads(roles.read_text())
        data[0].pop("secret")
        roles.write_text(json.dumps(data))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_broken_case_is_not_imported(self):
        err = StringIO()
        with override_settings(CASES_DIR=self.tmp):
            with self.assertRaisesMessage(CommandError, "1 case(s) not imported"):
                call_command("import_case", stdout=StringIO(), stderr=err)
        self.assertIn("'secret' is a required property", err.getvalue())
        self.assertFalse(Case.objects.exists())
