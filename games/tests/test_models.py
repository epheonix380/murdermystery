import datetime
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

    def game_for(self, host, **kwargs):
        return Game.objects.create(
            case=self.case, host=host, party_date=datetime.date(2030, 10, 31), player_count=4, **kwargs
        )

    def test_one_active_game_per_host(self):
        self.game_for(self.host)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.game_for(self.host, status=Game.Status.LIVE)

    def test_archiving_frees_the_slot(self):
        game = self.game_for(self.host)
        game.status = Game.Status.ARCHIVED
        game.save()
        self.game_for(self.host)
        self.game_for(Visitor.objects.create())
        self.assertEqual(Game.objects.count(), 3)

    def test_tokens_are_long_and_unique(self):
        game = self.game_for(self.host)
        a = Player.objects.create(game=game, display_name="Sam", role_id="WOLF")
        b = Player.objects.create(game=game, display_name="Alex", role_id="BREW")
        tokens = {game.gm_token, a.token, b.token}
        self.assertEqual(len(tokens), 3)
        self.assertTrue(all(len(t) >= 32 for t in tokens))

    def test_one_player_per_role(self):
        game = self.game_for(self.host)
        Player.objects.create(game=game, display_name="Sam", role_id="WOLF")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Player.objects.create(game=game, display_name="Alex", role_id="WOLF")

    def test_one_vote_per_player(self):
        game = self.game_for(self.host)
        sam = Player.objects.create(game=game, display_name="Sam", role_id="WOLF")
        Vote.objects.create(game=game, voter=sam, suspect_role_id="BREW")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Vote.objects.create(game=game, voter=sam, suspect_role_id="KEYS")


class ArchiveStaleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_case", "hollowpine", stdout=StringIO())
        cls.case = Case.objects.get(slug="hollowpine")

    def make(self, party_date):
        return Game.objects.create(case=self.case, host=Visitor.objects.create(), party_date=party_date, player_count=4)

    def test_archives_a_week_after_the_party(self):
        today = datetime.date(2030, 11, 10)
        old = self.make(datetime.date(2030, 11, 2))
        recent = self.make(datetime.date(2030, 11, 3))
        self.assertEqual(Game.archive_stale(today), 1)
        old.refresh_from_db()
        recent.refresh_from_db()
        self.assertEqual(old.status, Game.Status.ARCHIVED)
        self.assertEqual(recent.status, Game.Status.DRAFT)
