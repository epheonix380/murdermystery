import datetime
import json
from io import StringIO

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.cache import cache
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.urls import reverse

from catalog.models import Case
from games.engine import WRONG_GUESS_LIMIT, check_answer
from games.models import Game, Player
from mystery.asgi import application

CAST = [("Sam", "WOLF"), ("Alex", "BREW"), ("Jo", "FANG"), ("Kim", "KEYS")]
SECRET_STRINGS = ["103198", "10311998", "SIGHT", "kitchen\", \"mudroom", "Shift each letter back", "Marcus Reed killed Edgar"]


class CheckAnswerTests(SimpleTestCase):
    def test_digits(self):
        spec = {"type": "digits", "accept": ["103198", "10311998"]}
        for guess in ("103198", "10/31/98", "10-31-1998", " 10 31 98 "):
            self.assertTrue(check_answer(spec, guess), guess)
        for guess in ("1031", "103199", "", "ten thirty one"):
            self.assertFalse(check_answer(spec, guess), guess)

    def test_word(self):
        spec = {"type": "word", "accept": ["SIGHT"]}
        self.assertTrue(check_answer(spec, "sight"))
        self.assertTrue(check_answer(spec, "...out of his Sight."))
        self.assertFalse(check_answer(spec, "sightly"))
        self.assertFalse(check_answer(spec, "insight"))

    def test_route(self):
        spec = {"type": "route", "start": "great", "sequence": ["kitchen", "mudroom", "porch", "study"]}
        self.assertTrue(check_answer(spec, ["kitchen", "mudroom", "porch", "study"]))
        self.assertFalse(check_answer(spec, ["hallway", "study"]))
        self.assertFalse(check_answer(spec, "kitchen,mudroom,porch,study"))


class GameNightTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_case", "hollowpine", stdout=StringIO())
        cls.case = Case.objects.get(slug="hollowpine")

    def setUp(self):
        cache.clear()
        self.client.post(reverse("new-game", args=["hollowpine"]),
                         {"party_date": (datetime.date.today() + datetime.timedelta(days=1)).isoformat(), "player_count": 4})
        data = {"count": 4}
        for i, (name, role) in enumerate(CAST):
            data[f"name_{i}"], data[f"role_{i}"] = name, role
        self.client.post(reverse("host-players"), data)
        self.game = Game.objects.get()
        self.p = {p.role_id: p for p in self.game.players.all()}

    # helpers
    def act(self, action):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse("host-action"), json.dumps({"action": action}), content_type="application/json")

    def gm(self):
        return self.client.get(reverse("host-state")).json()

    def state(self, role):
        return self.client_class().get(reverse("player-state", args=[self.p[role].token])).json()

    def solve(self, role, puzzle, answer):
        return self.client_class().post(reverse("player-solve", args=[self.p[role].token]),
                                        json.dumps({"puzzle": puzzle, "answer": answer}), content_type="application/json").json()

    def vote(self, role, suspect):
        return self.client_class().post(reverse("player-vote", args=[self.p[role].token]),
                                        json.dumps({"suspect": suspect}), content_type="application/json")

    def assertNoSecrets(self, data):
        text = json.dumps(data)
        for s in SECRET_STRINGS:
            self.assertNotIn(s, text)

    # tests
    def test_nothing_unlocks_before_the_start(self):
        state = self.state("BREW")
        self.assertEqual(state, {"status": "invited", "round": 1, "rounds": 2})
        self.assertFalse(self.solve("BREW", "safe", "103198")["correct"])

    def test_full_game(self):
        self.assertEqual(self.act("start").status_code, 200)
        state = self.state("BREW")
        self.assertEqual(state["status"], "live")
        self.assertEqual([b["id"] for b in state["body"]], ["B1", "B2", "B3", "B4", "B5"])
        self.assertEqual(len(state["puzzles"]), 3)
        self.assertIn("WKH ZHUHZROI", state["puzzles"][1]["shows_text"])
        self.assertNoSecrets(state)
        self.assertEqual({s["location"]: s["open"] for s in state["sealed"]}["Ruth's Cabin"], False)

        # puzzles
        self.assertEqual(self.solve("FANG", "safe", "1234")["message"], "Not quite. Keep looking.")
        self.assertTrue(self.solve("FANG", "safe", "10/31/98")["correct"])
        self.assertTrue(self.solve("KEYS", "page", "out of his sight")["correct"])
        wrong = self.solve("KEYS", "route", ["hallway", "study"])
        self.assertEqual(wrong["message"], "Someone would have seen that. Try another way.")
        self.assertTrue(self.solve("KEYS", "route", ["kitchen", "mudroom", "porch", "study"])["correct"])
        state = self.state("BREW")
        self.assertTrue(all(p["solved"] for p in state["puzzles"]))
        self.assertEqual(state["puzzles"][0]["solved_by"], "Jo")
        opened = {s["location"]: s["open"] for s in state["sealed"]}
        self.assertTrue(opened["Edgar's Safe"] and opened["Guest Rooms"] and opened["Umbrella Stand"])

        # round 2
        self.assertEqual(self.act("next_round").status_code, 200)
        state = self.state("BREW")
        self.assertEqual(state["round"], 2)
        self.assertEqual(len(state["body"]), 8)
        self.assertTrue({s["location"]: s["open"] for s in state["sealed"]}["Ruth's Cabin"])
        self.assertEqual(self.act("next_round").json()["error"], "This is already the last round.")

        # voting
        self.assertEqual(self.vote("BREW", "WOLF").json()["error"], "Voting isn't open.")
        self.act("open_voting")
        voting = self.state("BREW")["voting"]
        self.assertEqual({s["role_id"] for s in voting["suspects"]}, {"WOLF", "FANG", "KEYS"})
        self.assertEqual(self.vote("BREW", "BREW").json()["error"], "You can't vote for yourself.")
        self.assertEqual(self.vote("BREW", "ROT").json()["error"], "That character isn't in this game.")
        self.assertEqual(self.vote("BREW", "WOLF").status_code, 200)
        self.assertEqual(self.vote("BREW", "FANG").json()["error"], "You've already voted.")
        self.vote("FANG", "WOLF")
        self.vote("KEYS", "FANG")
        self.vote("WOLF", "KEYS")
        self.assertEqual(self.state("BREW")["voting"]["your_vote"], "WOLF")

        gm = self.gm()
        self.assertEqual(gm["votes_in"], 4)
        self.assertNotIn("reveal", gm)  # the GM sees who voted, not how
        self.assertNotIn("tally", json.dumps(gm))

        # goals and reveal
        players = {p["name"]: p["id"] for p in gm["players"]}
        self.client.post(reverse("host-goal"), json.dumps({"player": players["Alex"], "met": True}), content_type="application/json")
        self.assertEqual(self.act("reveal").status_code, 200)
        reveal = self.state("KEYS")["reveal"]
        self.assertEqual(reveal["killer"], {"name": "Marcus Reed", "player": "Sam"})
        self.assertEqual(reveal["caught"], "yes")
        self.assertEqual(reveal["tally"][0], {"role_id": "WOLF", "name": "Marcus Reed", "player": "Sam", "votes": 2})
        self.assertTrue(reveal["text"].startswith("The scream at 11:20 was a recording"))
        goals = {g["player"]: g["met"] for g in reveal["goals"]}
        self.assertEqual(goals, {"Sam": None, "Alex": True, "Jo": None, "Kim": None})

    def test_tie_with_the_killer(self):
        self.act("start")
        self.act("open_voting")
        self.vote("BREW", "WOLF")
        self.vote("WOLF", "BREW")
        self.act("reveal")
        self.assertEqual(self.state("FANG")["reveal"]["caught"], "tie")

    def test_close_voting_returns_to_live(self):
        self.act("start")
        self.act("open_voting")
        self.assertEqual(self.act("close_voting").status_code, 200)
        self.assertEqual(self.state("BREW")["status"], "live")

    def test_actions_in_the_wrong_order(self):
        self.assertEqual(self.act("reveal").json()["error"], "Open voting before the reveal.")
        self.assertEqual(self.act("open_voting").json()["error"], "Voting can only open while the game is live.")
        self.act("start")
        self.assertEqual(self.act("start").json()["error"], "The game has already started.")
        self.assertEqual(self.act("explode").status_code, 400)

    def test_gm_state_has_answers_player_state_never_does(self):
        self.act("start")
        gm = self.gm()
        self.assertIn("103198", json.dumps(gm))
        self.assertTrue(gm["puzzles"][0]["explanation"])
        for status in ("live", "voting"):
            Game.objects.update(status=status)
            for role in self.p:
                self.assertNoSecrets(self.state(role))

    def test_wrong_guesses_are_limited(self):
        self.act("start")
        for _ in range(WRONG_GUESS_LIMIT):
            self.solve("BREW", "safe", "000000")
        result = self.solve("BREW", "safe", "103198")
        self.assertFalse(result["correct"])
        self.assertIn("Too many guesses", result["message"])
        self.assertTrue(self.solve("FANG", "safe", "103198")["correct"])  # limit is per player

    def test_only_the_host_can_run_the_game(self):
        stranger = self.client_class()
        for name in ("host-action", "host-goal"):
            response = stranger.post(reverse(name), json.dumps({"action": "start"}), content_type="application/json")
            self.assertEqual(response.status_code, 302)
        self.assertEqual(stranger.get(reverse("host-state")).status_code, 302)
        self.assertEqual(Game.objects.get().status, "invited")

    def test_ended_game_stops_answering(self):
        Game.objects.update(status="archived")
        self.assertEqual(self.client.get(reverse("player-state", args=[self.p["BREW"].token])).status_code, 404)

    def test_print_cards_follow_the_cast(self):
        html = self.client.get(reverse("host-print")).content.decode()
        self.assertIn("C01", html)
        self.assertIn("ITEM", html)
        self.assertNotIn("C09", html)  # needs Graham Pike, who isn't cast
        labels = self.client.get(reverse("host-print") + "?kind=labels").content.decode()
        self.assertIn("STUDY", labels)
        self.assertIn("RUTH&#x27;S CABIN", labels)


class LiveChannelTests(TransactionTestCase):
    # Channels' database helper closes connections between calls, which a
    # TestCase's wrapping transaction can't survive on Postgres.
    def setUp(self):
        call_command("import_case", "hollowpine", stdout=StringIO())

    async def test_phones_hear_about_changes(self):
        game, token = await sync_to_async(self._make_game)()
        phone = WebsocketCommunicator(application, f"/ws/p/{token}/", headers=[(b"origin", b"http://localhost")])
        connected, _ = await phone.connect()
        self.assertTrue(connected)
        from games.live import notify
        await sync_to_async(lambda: self._notify_now(notify, game))()
        self.assertEqual(await phone.receive_json_from(timeout=2), {"type": "changed"})
        await phone.disconnect()

    async def test_unknown_token_is_refused(self):
        phone = WebsocketCommunicator(application, "/ws/p/nope/", headers=[(b"origin", b"http://localhost")])
        connected, code = await phone.connect()
        self.assertFalse(connected)

    async def test_other_sites_are_refused(self):
        game, token = await sync_to_async(self._make_game)()
        phone = WebsocketCommunicator(application, f"/ws/p/{token}/", headers=[(b"origin", b"https://evil.example")])
        connected, _ = await phone.connect()
        self.assertFalse(connected)

    def _make_game(self):
        from games.models import Visitor
        game = Game.objects.create(case=Case.objects.get(), host=Visitor.objects.create(),
                                   party_date=datetime.date(2030, 1, 1), player_count=4, status="live")
        player = Player.objects.create(game=game, display_name="Sam", role_id="WOLF")
        return game, player.token

    def _notify_now(self, notify, game):
        notify(game)  # no wrapping transaction here, so on_commit runs at once
