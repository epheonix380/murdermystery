from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from catalog.models import Case
from games.models import Game, Player, Visitor, Vote


class GameRuleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_case", "hollowpine", stdout=StringIO())
        cls.case = Case.objects.get(slug="hollowpine")

    def setUp(self):
        self.host = Visitor.objects.create()

    def test_one_active_game_per_host(self):
        Game.objects.create(case=self.case, host=self.host)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Game.objects.create(case=self.case, host=self.host, status=Game.Status.LIVE)

    def test_archiving_frees_the_slot(self):
        game = Game.objects.create(case=self.case, host=self.host)
        game.status = Game.Status.ARCHIVED
        game.save()
        Game.objects.create(case=self.case, host=self.host)
        Game.objects.create(case=self.case, host=Visitor.objects.create())
        self.assertEqual(Game.objects.count(), 3)

    def test_tokens_are_long_and_unique(self):
        game = Game.objects.create(case=self.case, host=self.host)
        a = Player.objects.create(game=game, display_name="Sam", role_id="WOLF")
        b = Player.objects.create(game=game, display_name="Alex", role_id="BREW")
        tokens = {game.gm_token, a.token, b.token}
        self.assertEqual(len(tokens), 3)
        self.assertTrue(all(len(t) >= 32 for t in tokens))

    def test_one_player_per_role(self):
        game = Game.objects.create(case=self.case, host=self.host)
        Player.objects.create(game=game, display_name="Sam", role_id="WOLF")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(game=game, display_name="Alex", role_id="WOLF")

    def test_one_vote_per_player(self):
        game = Game.objects.create(case=self.case, host=self.host)
        sam = Player.objects.create(game=game, display_name="Sam", role_id="WOLF")
        Vote.objects.create(game=game, voter=sam, suspect_role_id="BREW")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(game=game, voter=sam, suspect_role_id="KEYS")
