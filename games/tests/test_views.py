import datetime
import json
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalog.models import Case
from games.models import Game, Player, Visitor
from games.visitor import COOKIE

HOLLOWPINE = settings.CASES_DIR / "hollowpine"
PARTY = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_case", "hollowpine", stdout=StringIO())
        cls.case = Case.objects.get(slug="hollowpine")

    def create_game(self, count=4):
        return self.client.post(reverse("new-game", args=["hollowpine"]), {"party_date": PARTY, "player_count": count})

    def save_cast(self, rows, count=None, player_ids=None):
        data = {"count": count or len(rows)}
        for i, (name, role) in enumerate(rows):
            data[f"name_{i}"] = name
            data[f"role_{i}"] = role
            if player_ids:
                data[f"player_{i}"] = player_ids[i]
        return self.client.post(reverse("host-players"), data)


class CaseBrowserTests(Base):
    def test_lists_published_cases_with_map_and_counts(self):
        html = self.client.get("/").content.decode()
        self.assertIn("The Last Chapter at Hollowpine Lodge", html)
        self.assertIn('src="/cases/hollowpine/public/map.svg"', html)
        for text in ("4–7", "44", "clues", "puzzles", "props"):
            self.assertIn(text, html)

    def test_hides_draft_cases(self):
        Case.objects.update(published=False)
        self.assertNotIn("Hollowpine", self.client.get("/").content.decode())
        self.assertEqual(self.client.get(reverse("new-game", args=["hollowpine"])).status_code, 404)

    def test_browsing_creates_no_visitor(self):
        self.client.get("/")
        self.client.get(reverse("new-game", args=["hollowpine"]))
        self.assertFalse(Visitor.objects.exists())
        self.assertNotIn(COOKIE, self.client.cookies)


class HostingTests(Base):
    def test_creating_a_game_sets_the_visitor_cookie(self):
        response = self.create_game()
        self.assertRedirects(response, reverse("host-players"))
        visitor = Visitor.objects.get()
        self.assertEqual(self.client.cookies[COOKIE].value, str(visitor.pk))
        self.assertTrue(self.client.cookies[COOKIE]["httponly"])
        game = Game.objects.get()
        self.assertEqual((game.host, game.player_count, game.status), (visitor, 4, "draft"))

    def test_rejects_past_date_and_bad_count(self):
        response = self.client.post(reverse("new-game", args=["hollowpine"]), {"party_date": "2000-01-01", "player_count": 9})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "can&#x27;t be in the past")
        self.assertContains(response, "Select a valid choice")
        self.assertFalse(Game.objects.exists())

    def test_one_active_game(self):
        self.create_game()
        response = self.create_game()
        self.assertRedirects(response, reverse("host"))
        self.assertEqual(Game.objects.count(), 1)
        self.assertNotContains(self.client.get("/"), "Host this case")

    def test_host_pages_need_an_active_game(self):
        for name in ("host", "host-players", "host-links"):
            self.assertRedirects(self.client.get(reverse(name)), reverse("home"))

    def test_another_visitor_cannot_see_the_game(self):
        self.create_game()
        other = self.client_class()
        self.assertRedirects(other.get(reverse("host")), reverse("home"))

    def test_save_cast_and_links(self):
        self.create_game()
        response = self.save_cast([("Sam", "WOLF"), ("Alex", ""), ("Jo", ""), ("Kim", "")])
        self.assertRedirects(response, reverse("host-links"))
        game = Game.objects.get()
        self.assertEqual(game.status, "invited")
        self.assertEqual(game.players.get(display_name="Sam").role_id, "WOLF")
        self.assertEqual({p.role_id for p in game.players.all()}, {"WOLF", "BREW", "FANG", "KEYS"})

        links = self.client.get(reverse("host-links")).content.decode()
        for p in game.players.all():
            self.assertIn(f"http://testserver/p/{p.token}/", links)

    def test_cast_errors_are_shown(self):
        self.create_game()
        response = self.save_cast([("Sam", "ROT"), ("Alex", ""), ("Jo", ""), ("Kim", "")])
        self.assertContains(response, "Every core character must be played")
        self.assertFalse(Player.objects.exists())

    def test_editing_cast_keeps_links(self):
        self.create_game()
        self.save_cast([("Sam", "WOLF"), ("Alex", "BREW"), ("Jo", "FANG"), ("Kim", "KEYS")])
        players = list(Game.objects.get().players.order_by("id"))
        tokens = {p.display_name: p.token for p in players}
        ids = [str(p.pk) for p in players]

        # Swap Sam and Alex's roles, rename Kim, drop Jo, add Lee.
        rows = [("Sam", "BREW"), ("Alex", "WOLF"), ("Kimberly", "KEYS"), ("Lee", "FANG")]
        self.save_cast(rows, player_ids=[ids[0], ids[1], ids[3], ""])

        after = {p.display_name: p for p in Game.objects.get().players.all()}
        self.assertEqual(set(after), {"Sam", "Alex", "Kimberly", "Lee"})
        self.assertEqual(after["Sam"].token, tokens["Sam"])
        self.assertEqual(after["Sam"].role_id, "BREW")
        self.assertEqual(after["Alex"].role_id, "WOLF")
        self.assertEqual(after["Kimberly"].token, tokens["Kim"])
        self.assertNotIn(after["Lee"].token, tokens.values())
        self.assertFalse(Player.objects.filter(token=tokens["Jo"]).exists())

    def test_cast_locked_once_live(self):
        self.create_game()
        Game.objects.update(status="live")
        self.assertRedirects(self.client.get(reverse("host-players")), reverse("host"))

    def test_end_game_frees_the_slot(self):
        self.create_game()
        self.assertEqual(self.client.get(reverse("host-end")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("host-end")), reverse("home"))
        self.assertEqual(Game.objects.get().status, "archived")
        self.assertRedirects(self.create_game(), reverse("host-players"))

    def test_gm_link_restores_access_on_a_new_device(self):
        self.create_game()
        game = Game.objects.get()
        phone = self.client_class()
        self.assertRedirects(phone.get(reverse("gm-link", args=[game.gm_token])), reverse("host"))
        self.assertContains(phone.get(reverse("host")), "Hollowpine")

    def test_gm_link_stops_working_after_the_game(self):
        self.create_game()
        game = Game.objects.get()
        Game.objects.update(status="archived")
        self.assertEqual(self.client_class().get(reverse("gm-link", args=[game.gm_token])).status_code, 404)

    def test_bad_cookie_is_ignored(self):
        self.client.cookies[COOKIE] = "not-a-uuid"
        self.assertEqual(self.client.get("/").status_code, 200)


class PlayerSheetTests(Base):
    def setUp(self):
        self.create_game(5)
        self.save_cast([("Sam", "WOLF"), ("Alex", "BREW"), ("Jo", "FANG"), ("Kim", "KEYS"), ("Lee", "ROT")])
        self.players = {p.role_id: p for p in Player.objects.all()}
        self.roles = {r["id"]: r for r in json.loads((HOLLOWPINE / "roles.json").read_text())}
        self.solution = json.loads((HOLLOWPINE / "solution.json").read_text())
        self.puzzles = json.loads((HOLLOWPINE / "puzzles.json").read_text())

    def sheet(self, role_id):
        response = self.client_class().get(reverse("player", args=[self.players[role_id].token]))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_shows_own_sheet(self):
        html = self.sheet("BREW")
        role = self.roles["BREW"]
        self.assertIn(role["name"], html)
        self.assertIn("Hi Alex", html)
        for text in (role["costume"], role["timeline"][0]["text"]):
            self.assertIn(text.replace('"', "&quot;").replace("'", "&#x27;"), html)
        self.assertNotIn("YOU ARE THE KILLER", html)

    def test_killer_is_told(self):
        self.assertIn("YOU ARE THE KILLER", self.sheet("WOLF"))

    def test_never_shows_other_secrets_or_the_solution(self):
        for role_id in self.players:
            html = self.sheet(role_id)
            for other_id, other in self.roles.items():
                if other_id == role_id:
                    continue
                for field in ("secret", "goal"):
                    if other[field] in (self.roles[role_id]["secret"], self.roles[role_id]["goal"]):
                        continue  # two roles can share the same text, e.g. a goal
                    snippet = other[field][:40].replace('"', "&quot;").replace("'", "&#x27;")
                    self.assertNotIn(snippet, html, f"{role_id} sees {other_id}'s {field}")
            self.assertNotIn(self.solution["reveal"][:40], html)
            self.assertNotIn("103198", html)
            self.assertNotIn("SIGHT", html)

    def test_lists_the_cast_without_secrets(self):
        html = self.sheet("BREW")
        for name in ("Sam", "Jo", "Kim", "Lee", "Marcus Reed", "Graham Pike", "Edgar Thorne"):
            self.assertIn(name, html)
        self.assertNotIn("Madame Oriel", html)  # not cast in this game

    def test_unknown_token(self):
        self.assertEqual(self.client.get(reverse("player", args=["nope"])).status_code, 404)

    def test_records_last_seen(self):
        self.sheet("BREW")
        self.players["BREW"].refresh_from_db()
        self.assertIsNotNone(self.players["BREW"].last_seen)

    def test_ended_game(self):
        Game.objects.update(status="archived")
        html = self.sheet("BREW")
        self.assertIn("This game has ended", html)
        self.assertNotIn(self.roles["BREW"]["secret"][:30], html)

    def test_not_indexed(self):
        self.assertIn('content="noindex, nofollow"', self.sheet("BREW"))
