"""Play a whole game of a case automatically, then undo it.

This checks what import_case can't: that the case actually plays. For the
smallest and largest cast it starts a game, opens every round, solves every
puzzle with its own answer (and checks a wrong answer is refused), votes,
reveals, and checks no player's phone was ever sent another character's
secrets, a puzzle answer or the solution before the reveal. Nothing is kept.
"""

import datetime
import json
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.importer import import_case
from catalog.loader import CaseError, bundle_for
from games import engine
from games.casting import cast_roles
from games.models import Game, Player, Visitor


class Rollback(Exception):
    pass


def known_answer(answer):
    return answer["sequence"] if answer["type"] == "route" else answer["accept"][0]


def wrong_answer(answer):
    if answer["type"] == "route":
        return list(reversed(answer["sequence"]))
    return "0" if answer["type"] == "digits" else "zzqx"


def secrets_of(bundle):
    """Text a player must never receive before the reveal, keyed by what it is."""
    out = {}
    for p in bundle.puzzles:
        a = p["answer"]
        if a["type"] != "route":  # route answers are room ids, which the map shows anyway
            for value in a["accept"]:
                out[f"answer to puzzle {p['id']!r}"] = value
        if p.get("explanation"):
            out[f"explanation of puzzle {p['id']!r}"] = p["explanation"]
    out["reveal text"] = bundle.solution["reveal"]
    if bundle.solution.get("summary"):
        out["solution summary"] = bundle.solution["summary"]
    return out


class Command(BaseCommand):
    help = "Play a full game of a case automatically (smallest and largest cast), then undo it."

    def add_arguments(self, parser):
        parser.add_argument("case", help="A case folder, or a slug inside CASES_DIR")

    def handle(self, *args, case, **options):
        folder = Path(case) if Path(case).is_dir() else settings.CASES_DIR / case
        if not (folder / "case.json").is_file():
            raise CommandError(f"{case}: no case.json found")
        problems = []
        try:
            with transaction.atomic():
                try:
                    case_row = import_case(folder, published=False)
                except CaseError as e:
                    raise CommandError("import_case finds problems; fix them first:\n  - " + "\n  - ".join(e.problems))
                bundle = bundle_for(case_row)
                self.report(bundle)
                for count in sorted({case_row.min_players, case_row.max_players}):
                    problems += [f"{count} players: {p}" for p in self.play(case_row, bundle, count)]
                raise Rollback
        except Rollback:
            pass
        if problems:
            raise CommandError("Playtest found problems:\n  - " + "\n  - ".join(problems))
        self.stdout.write(self.style.SUCCESS("Playtest passed. Nothing was saved."))

    def report(self, b):
        w = self.stdout.write
        w(f"{b.manifest['title']}: {len(b.roles)} roles ({sum(r['core'] for r in b.roles)} core), "
          f"{b.manifest['min_players']}-{b.manifest['max_players']} players, {b.clues['rounds']} rounds")
        for rnd in range(1, b.clues["rounds"] + 1):
            body = sum(1 for c in b.clues.get("body", []) if c["round"] == rnd)
            cards = sum(1 for c in b.clues.get("cards", []) if c["round"] == rnd)
            w(f"  round {rnd}: {body} body clues, {cards} clue cards")
        for s in b.clues.get("sealed", []):
            how = f"puzzle {s['unlocked_by_puzzle']}" if "unlocked_by_puzzle" in s else f"round {s['unlocked_by_round']}"
            n = sum(1 for c in b.clues.get("cards", []) if c["location"] == s["location"])
            w(f"  sealed {s['location']}: {n} cards, opened by {how}")
            if n == 0:
                self.stderr.write(self.style.WARNING(f"  warning: nothing is sealed in {s['location']}"))
        killer = b.role(b.solution["killer"])
        w(f"  killer: {killer['name']} ({killer['id']})")

    def play(self, case_row, bundle, count):
        problems = []
        game = Game.objects.create(case=case_row, host=Visitor.objects.create(),
                                   party_date=datetime.date.today(), player_count=count, status=Game.Status.INVITED)
        cast = cast_roles(bundle.roles, case_row.min_players, case_row.max_players,
                          [(f"Player {i + 1}", "") for i in range(count)])
        players = [Player.objects.create(game=game, display_name=n, role_id=r) for n, r in cast]
        others = {
            p.pk: {f"{r['name']}'s {field}": r[field]
                   for r in bundle.roles if r["id"] != p.role_id
                   for field in ("secret", "goal")
                   if r[field] not in (bundle.role(p.role_id)["secret"], bundle.role(p.role_id)["goal"])}
            for p in players
        }
        hidden = secrets_of(bundle)

        def check_phones(stage):
            for p in players:
                text = json.dumps(engine.player_state(game, p, bundle))
                for what, value in {**hidden, **others[p.pk]}.items():
                    if value and value in text:
                        problems.append(f"{stage}: {p.display_name}'s phone was sent the {what}")

        def must(error, doing):
            if error:
                problems.append(f"{doing}: {error}")

        check_phones("before the start")
        must(engine.start(game, bundle), "starting")
        for rnd in range(1, bundle.clues["rounds"] + 1):
            if rnd > 1:
                must(engine.next_round(game, bundle), f"starting round {rnd}")
            check_phones(f"round {rnd}")
        for i, puzzle in enumerate(bundle.puzzles):
            solver = players[i % len(players)]
            ok, msg = engine.solve(game, solver, bundle, puzzle["id"], wrong_answer(puzzle["answer"]))
            if ok:
                problems.append(f"puzzle {puzzle['id']!r} accepted a wrong answer")
            ok, msg = engine.solve(game, solver, bundle, puzzle["id"], known_answer(puzzle["answer"]))
            if not ok:
                problems.append(f"puzzle {puzzle['id']!r} refused its own answer: {msg}")
            cache.delete(f"wrong-guesses:{solver.pk}")
        closed = [s["location"] for s in engine.gm_state(game, bundle)["sealed"] if not s["open"]]
        if closed:
            problems.append(f"still sealed after every puzzle and round: {', '.join(closed)}")
        check_phones("after the puzzles")

        must(engine.open_voting(game, bundle), "opening voting")
        killer = bundle.solution["killer"]
        for p in players:
            suspect = killer if p.role_id != killer else next(q.role_id for q in players if q.role_id != killer)
            must(engine.vote(game, p, bundle, suspect), f"{p.display_name} voting")
        check_phones("during voting")
        must(engine.reveal(game, bundle), "revealing")
        caught = engine.player_state(game, players[0], bundle)["reveal"]["caught"]
        if caught != "yes":
            problems.append(f"everyone voted for the killer but the reveal says caught={caught!r}")
        self.stdout.write(f"  played with {count} players: {', '.join(bundle.role(p.role_id)['name'] for p in players)}")
        return problems
