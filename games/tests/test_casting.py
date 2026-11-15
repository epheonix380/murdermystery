import random

from django.conf import settings
from django.test import SimpleTestCase

from catalog.loader import load_case
from games.casting import CastingError, cast_roles

ROLES = load_case(settings.CASES_DIR / "hollowpine").roles
CORE = {"WOLF", "BREW", "FANG", "KEYS"}
OPTIONAL = {"ROT", "ORB", "BOO"}


def cast(rows, seed=0):
    return cast_roles(ROLES, 4, 7, rows, rng=random.Random(seed))


class CastRolesTests(SimpleTestCase):
    def test_all_random_casts_every_core_role(self):
        for seed in range(20):
            result = cast([("A", ""), ("B", ""), ("C", ""), ("D", "")], seed)
            self.assertEqual({r for _, r in result}, CORE)

    def test_extra_players_get_optional_roles(self):
        result = cast([(n, "") for n in "ABCDEF"])
        roles = {r for _, r in result}
        self.assertTrue(CORE <= roles)
        self.assertEqual(len(roles & OPTIONAL), 2)

    def test_keeps_chosen_roles_and_order(self):
        result = cast([("Sam", ""), ("Alex", "WOLF"), ("Jo", ""), ("Kim", "ROT"), ("Lee", "")])
        self.assertEqual(result[1], ("Alex", "WOLF"))
        self.assertEqual(result[3], ("Kim", "ROT"))
        self.assertEqual([n for n, _ in result], ["Sam", "Alex", "Jo", "Kim", "Lee"])
        self.assertTrue(CORE <= {r for _, r in result})

    def test_names_are_trimmed(self):
        self.assertEqual(cast([("  Sam ", "WOLF"), ("B", ""), ("C", ""), ("D", "")])[0][0], "Sam")

    def assertCastingError(self, rows, fragment):
        with self.assertRaises(CastingError) as ctx:
            cast(rows)
        self.assertTrue(any(fragment in p for p in ctx.exception.problems), ctx.exception.problems)

    def test_too_few_players(self):
        self.assertCastingError([("A", ""), ("B", ""), ("C", "")], "needs 4 to 7 players")

    def test_too_many_players(self):
        self.assertCastingError([(n, "") for n in "ABCDEFGH"], "needs 4 to 7 players")

    def test_blank_name(self):
        self.assertCastingError([("A", ""), ("", ""), ("C", ""), ("D", "")], "needs a name")

    def test_duplicate_name(self):
        self.assertCastingError([("Sam", ""), ("sam", ""), ("C", ""), ("D", "")], "same name")

    def test_same_role_twice(self):
        self.assertCastingError([("A", "WOLF"), ("B", "WOLF"), ("C", ""), ("D", "")], "picked for two players")

    def test_unknown_role(self):
        self.assertCastingError([("A", "GHOST"), ("B", ""), ("C", ""), ("D", "")], "not a role")

    def test_optional_role_crowding_out_core(self):
        self.assertCastingError([("A", "ROT"), ("B", ""), ("C", ""), ("D", "")], "Every core character must be played")
