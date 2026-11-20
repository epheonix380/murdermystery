import datetime
import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.urls import reverse

from catalog.importer import import_case
from games.models import Game, Player, Visitor

MINICASE = Path(__file__).parent / "fixtures" / "minicase"


def run(*args):
    out = StringIO()
    call_command(*args, stdout=out, stderr=StringIO())
    return out.getvalue()


class PlaytestTests(TestCase):
    def test_hollowpine_plays(self):
        output = run("playtest_case", "hollowpine")
        self.assertIn("played with 4 players", output)
        self.assertIn("played with 7 players", output)
        self.assertIn("Nothing was saved", output)

    def test_example_case_plays(self):
        self.assertIn("Playtest passed", run("playtest_case", str(MINICASE)))

    def test_leaves_nothing_behind(self):
        from catalog.models import Case
        run("playtest_case", str(MINICASE))
        self.assertFalse(Case.objects.exists())
        self.assertFalse(Game.objects.exists())


class BrokenPlaytestTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.folder = self.tmp / "minicase"
        shutil.copytree(MINICASE, self.folder)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit(self, name, change):
        path = self.folder / name
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def assertPlaytestFinds(self, fragment):
        with self.assertRaises(CommandError) as ctx:
            run("playtest_case", str(self.folder))
        self.assertIn(fragment, str(ctx.exception))

    def test_answer_given_away_in_a_prompt(self):
        self.edit("puzzles.json", lambda ps: ps[0].update(prompt="The code is 1887."))
        self.assertPlaytestFinds("phone was sent the answer to puzzle 'cellar'")

    def test_solution_given_away_on_a_body_clue(self):
        def leak(clues):
            clues["body"][0]["text"] = json.loads((self.folder / "solution.json").read_text())["reveal"]
        self.edit("clues.json", leak)
        self.assertPlaytestFinds("phone was sent the reveal text")

    def test_other_roles_secret_on_a_clue(self):
        def leak(clues):
            roles = json.loads((self.folder / "roles.json").read_text())
            clues["body"][0]["text"] = roles[0]["secret"]
        self.edit("clues.json", leak)
        self.assertPlaytestFinds("Hollis Grey's secret")

    def test_invalid_case_is_sent_back_to_import_case(self):
        self.edit("solution.json", lambda s: s.update(killer="GUEST"))
        self.assertPlaytestFinds("import_case finds problems")


class RenderMapTests(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.folder = self.tmp / "minicase"
        shutil.copytree(MINICASE, self.folder)
        (self.folder / "public" / "map.svg").unlink()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_draws_rooms_doors_walls_and_labels(self):
        run("render_map", str(self.folder))
        svg = (self.folder / "public" / "map.svg").read_text()
        for text in ("Wine Cellar", "Butler's Room", "Stair down", 'stroke-width="3"', 'stroke-dasharray="6 4"', "Locked"):
            self.assertIn(text, svg)
        self.assertIn('aria-label="Floor plan of The Last Toast at Briar Hall"', svg)

    def test_needs_a_map(self):
        self.edit_extras(lambda e: e.pop("map"))
        with self.assertRaises(CommandError):
            run("render_map", str(self.folder))

    def edit_extras(self, change):
        path = self.folder / "extras.json"
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def test_escapes_text(self):
        self.edit_extras(lambda e: e["map"]["rooms"][0].update(name="<Garden & Co>"))
        run("render_map", str(self.folder))
        self.assertIn("&lt;Garden &amp; Co&gt;", (self.folder / "public" / "map.svg").read_text())


class StartingPropTests(TestCase):
    def test_sheet_and_dashboard_show_who_starts_with_a_prop(self):
        case = import_case(MINICASE)
        host = Visitor.objects.create()
        game = Game.objects.create(case=case, host=host, party_date=datetime.date.today(), player_count=3, status="invited")
        clara = Player.objects.create(game=game, display_name="Ana", role_id="HEIR")
        Player.objects.create(game=game, display_name="Ben", role_id="BUTLER")
        Player.objects.create(game=game, display_name="Cy", role_id="DOCTOR")

        sheet = self.client.get(reverse("player", args=[clara.token])).content.decode()
        self.assertIn("You start with", sheet)
        self.assertIn("The Sealed Will", sheet)
        butler = Player.objects.get(role_id="BUTLER")
        self.assertNotIn("You start with", self.client_class().get(reverse("player", args=[butler.token])).content.decode())

        self.client.cookies["mm_visitor"] = str(host.pk)
        dashboard = self.client.get(reverse("host")).content.decode()
        self.assertIn("Clara Voss (Ana)", dashboard)
        self.assertIn("Wine Cellar", dashboard)
