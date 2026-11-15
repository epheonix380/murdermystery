import json
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from catalog.loader import CaseError, case_folders, load_case

HOLLOWPINE = settings.CASES_DIR / "hollowpine"


class BrokenCaseMixin:
    """Copies Hollowpine to a temp folder so each test can break one thing."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.folder = self.tmp / "hollowpine"
        shutil.copytree(HOLLOWPINE, self.folder)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit(self, name, change):
        path = self.folder / name
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def assertProblem(self, fragment):
        with self.assertRaises(CaseError) as ctx:
            load_case(self.folder)
        self.assertTrue(
            any(fragment in p for p in ctx.exception.problems),
            f"{fragment!r} not in {ctx.exception.problems}",
        )


class HollowpineTests(SimpleTestCase):
    def test_loads(self):
        case = load_case(HOLLOWPINE)
        self.assertEqual(case.slug, "hollowpine")
        self.assertEqual(len(case.roles), 7)
        self.assertEqual(case.clue_count, 44)
        self.assertEqual(len(case.puzzles), 3)
        self.assertEqual(len(case.props), 2)
        self.assertEqual(case.solution["killer"], "WOLF")
        self.assertEqual(case.map_url, "/cases/hollowpine/public/map.svg")

    def test_player_range_matches_roles(self):
        case = load_case(HOLLOWPINE)
        core = [r for r in case.roles if r["core"]]
        self.assertEqual(case.manifest["min_players"], len(core))
        self.assertEqual(case.manifest["max_players"], len(case.roles))

    def test_found_by_case_folders(self):
        self.assertIn(HOLLOWPINE, case_folders())


class SchemaProblemTests(BrokenCaseMixin, SimpleTestCase):
    def test_missing_required_field(self):
        self.edit("roles.json", lambda roles: roles[0].pop("goal"))
        self.assertProblem("'goal' is a required property")

    def test_wrong_type(self):
        self.edit("case.json", lambda m: m.update(min_players="four"))
        self.assertProblem("case.json min_players")

    def test_unknown_answer_type(self):
        self.edit("puzzles.json", lambda ps: ps[0]["answer"].update(type="riddle"))
        self.assertProblem("puzzles.json 0/answer")

    def test_invalid_json(self):
        (self.folder / "clues.json").write_text("{ not json")
        self.assertProblem("clues.json: not valid JSON")

    def test_missing_file(self):
        (self.folder / "props.json").unlink()
        self.assertProblem("props.json: file not found")

    def test_file_outside_folder(self):
        self.edit("case.json", lambda m: m["files"].update(roles="../../etc/passwd"))
        self.assertProblem("is outside the case folder")

    def test_reports_every_problem_at_once(self):
        self.edit("roles.json", lambda roles: roles[0].pop("goal"))
        self.edit("solution.json", lambda s: s.pop("reveal"))
        with self.assertRaises(CaseError) as ctx:
            load_case(self.folder)
        self.assertEqual(len(ctx.exception.problems), 2)


class CrossCheckTests(BrokenCaseMixin, SimpleTestCase):
    def test_killer_must_exist(self):
        self.edit("solution.json", lambda s: s.update(killer="NOBODY"))
        self.assertProblem("'NOBODY' is not a role id")

    def test_killer_must_be_core(self):
        self.edit("solution.json", lambda s: s.update(killer="ROT"))
        self.assertProblem("must be a core role")

    def test_duplicate_role(self):
        self.edit("roles.json", lambda roles: roles.append(dict(roles[0])))
        self.assertProblem("id 'WOLF' is used more than once")

    def test_min_players_below_core_roles(self):
        self.edit("case.json", lambda m: m.update(min_players=2))
        self.assertProblem("fewer than the 4 core roles")

    def test_max_players_above_roles(self):
        self.edit("case.json", lambda m: m.update(max_players=9))
        self.assertProblem("more than the 7 roles")

    def test_clue_round_past_last_round(self):
        self.edit("clues.json", lambda c: c["cards"][0].update(round=3))
        self.assertProblem("past the last round")

    def test_clue_requires_unknown_role(self):
        self.edit("clues.json", lambda c: c["cards"][0].update(requires_role="WOLF"))
        self.assertProblem("is not an optional role")

    def test_puzzle_unlocks_unknown_location(self):
        self.edit("puzzles.json", lambda ps: ps[0].update(unlocks="The Attic"))
        self.assertProblem("'The Attic', which is not a sealed location")

    def test_route_room_must_be_on_map(self):
        self.edit("puzzles.json", lambda ps: ps[2]["answer"]["sequence"].append("attic"))
        self.assertProblem("route room 'attic'")

    def test_prop_clue_must_exist(self):
        self.edit("props.json", lambda ps: ps[0].update(clue="C99"))
        self.assertProblem("clue 'C99' is not a clue id")

    def test_starting_prop_must_exist(self):
        self.edit("roles.json", lambda roles: roles[0].update(starting_props=["dagger"]))
        self.assertProblem("starting prop 'dagger'")

    def test_slug_matches_folder(self):
        self.edit("case.json", lambda m: m.update(slug="other"))
        self.assertProblem("does not match the folder name")

    def test_map_must_be_public(self):
        self.edit("case.json", lambda m: m.update(map="roles.json"))
        self.assertProblem("must be an https:// link or a file under public/")

    def test_map_file_must_exist(self):
        (self.folder / "public" / "map.svg").unlink()
        self.assertProblem("public/map.svg not found")
