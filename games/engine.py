"""The rules of game night: what each person may see, and what may happen next.

Every function that changes a game returns an error message for the person
who tried it, or None when it worked. Views turn these into JSON and tell
the game's live channel that something changed.
"""

import re
from collections import Counter

from django.core.cache import cache
from django.db import IntegrityError, transaction

from .models import Game, PuzzleSolve, Vote

S = Game.Status
PLAYING = (S.LIVE, S.VOTING, S.REVEALED)

WRONG_GUESS_LIMIT = 8
WRONG_GUESS_WINDOW = 60  # seconds


# ---------- answers ----------

def check_answer(answer, submission):
    """Whether `submission` solves a puzzle whose answer spec is `answer`."""
    kind = answer["type"]
    if kind == "digits":
        return re.sub(r"\D", "", str(submission)) in answer["accept"]
    if kind == "word":
        text = str(submission)
        return any(re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE) for w in answer["accept"])
    if kind == "route":
        return isinstance(submission, list) and [str(s) for s in submission] == answer["sequence"]
    return False


def route_hint(answer, submission):
    """A nudge for a wrong route, like the original site gave."""
    if not submission:
        return "Tap the rooms in order."
    if submission[-1] != answer["sequence"][-1]:
        return "The route has to end where the crime happened."
    return "Someone would have seen that. Try another way."


# ---------- what people can see ----------

def _cast(game, bundle):
    roles = {r["id"]: r for r in bundle.roles}
    return [(p, roles[p.role_id]) for p in game.players.order_by("id") if p.role_id in roles]


def _puzzles(game, bundle, for_gm):
    solves = {s.puzzle_id: s for s in game.solves.select_related("solved_by")}
    out = []
    for p in bundle.puzzles:
        solve = solves.get(p["id"])
        item = {
            "id": p["id"],
            "title": p["title"],
            "prompt": p["prompt"],
            "hint": p.get("hint", ""),
            "type": p["answer"]["type"],
            "unlocks": p.get("unlocks", ""),
            "solved": solve is not None,
            "solved_by": solve.solved_by.display_name if solve and solve.solved_by else "",
        }
        shows = p.get("shows")
        if shows and shows != "map":
            item["shows_text"] = bundle.extras.get(shows, "")
        if p["answer"]["type"] == "route":
            item["start"] = p["answer"]["start"]
        if for_gm:
            item["answer"] = p["answer"]
            item["explanation"] = p.get("explanation", "")
            item["solved_at"] = solve.solved_at.isoformat() if solve else None
        out.append(item)
    return out


def _sealed(game, bundle):
    solved = set(game.solves.values_list("puzzle_id", flat=True))
    out = []
    for s in bundle.clues.get("sealed", []):
        if "unlocked_by_puzzle" in s:
            is_open = s["unlocked_by_puzzle"] in solved
        else:
            is_open = game.status in PLAYING and game.current_round >= s["unlocked_by_round"]
        out.append({"location": s["location"], "instructions": s["instructions"], "open": is_open})
    return out


def tally(game, bundle):
    cast = _cast(game, bundle)
    counts = Counter(game.votes.values_list("suspect_role_id", flat=True))
    rows = sorted(
        ({"role_id": role["id"], "name": role["name"], "player": p.display_name, "votes": counts.get(role["id"], 0)}
         for p, role in cast),
        key=lambda r: -r["votes"],
    )
    killer = bundle.solution["killer"]
    top = max((r["votes"] for r in rows), default=0)
    leaders = [r["role_id"] for r in rows if r["votes"] == top and top > 0]
    if leaders == [killer]:
        caught = "yes"
    elif killer in leaders:
        caught = "tie"
    else:
        caught = "no"
    return rows, caught


def _reveal(game, bundle):
    rows, caught = tally(game, bundle)
    killer_id = bundle.solution["killer"]
    cast = _cast(game, bundle)
    killer = next(({"name": r["name"], "player": p.display_name} for p, r in cast if r["id"] == killer_id), None)
    return {
        "killer": killer,
        "caught": caught,
        "tally": rows,
        "summary": bundle.solution.get("summary", ""),
        "text": bundle.solution["reveal"],
        "timeline": bundle.solution.get("timeline", []),
        "goals": [{"name": r["name"], "player": p.display_name, "goal": r["goal"], "met": p.goal_met} for p, r in cast],
    }


def _voting(game, bundle, player):
    vote = game.votes.filter(voter=player).first()
    return {
        "suspects": [{"role_id": r["id"], "name": r["name"], "player": p.display_name}
                     for p, r in _cast(game, bundle) if p.pk != player.pk],
        "your_vote": vote.suspect_role_id if vote else None,
        "votes_in": game.votes.count(),
        "players": game.players.count(),
    }


def player_state(game, player, bundle):
    """Everything one player's phone may show right now, and nothing more."""
    state = {"status": game.status, "round": game.current_round, "rounds": bundle.clues["rounds"]}
    if game.status not in PLAYING:
        return state
    revealed = game.status == S.REVEALED
    state["body"] = [
        {"id": b["id"], "round": b["round"], "label": b["label"], "text": b["text"]}
        for b in bundle.clues.get("body", [])
        if revealed or b["round"] <= game.current_round
    ]
    state["puzzles"] = _puzzles(game, bundle, for_gm=False)
    state["sealed"] = [{"location": s["location"], "open": s["open"]} for s in _sealed(game, bundle)]
    if game.status == S.VOTING:
        state["voting"] = _voting(game, bundle, player)
    if revealed:
        state["reveal"] = _reveal(game, bundle)
    return state


def gm_state(game, bundle):
    voted = set(game.votes.values_list("voter_id", flat=True))
    names = {r["id"]: r["name"] for r in bundle.roles}
    state = {
        "status": game.status,
        "round": game.current_round,
        "rounds": bundle.clues["rounds"],
        "players": [
            {"id": p.pk, "name": p.display_name, "character": names.get(p.role_id, p.role_id),
             "seen": p.last_seen.isoformat() if p.last_seen else None, "voted": p.pk in voted, "goal_met": p.goal_met}
            for p in game.players.order_by("id")
        ],
        "puzzles": _puzzles(game, bundle, for_gm=True),
        "sealed": _sealed(game, bundle),
        "votes_in": len(voted),
    }
    if game.status == S.REVEALED:
        state["reveal"] = _reveal(game, bundle)
    return state


# ---------- changes ----------

def _move(game, from_statuses, **changes):
    """Change the game only if it is still in one of `from_statuses`."""
    with transaction.atomic():
        updated = Game.objects.filter(pk=game.pk, status__in=from_statuses).update(**changes)
    game.refresh_from_db()
    return updated == 1


def start(game, bundle):
    if not game.players.exists():
        return "Add your players before starting."
    if not _move(game, [S.INVITED], status=S.LIVE, current_round=1):
        return "The game has already started."


def next_round(game, bundle):
    if game.status != S.LIVE:
        return "Rounds can only move on while the game is live."
    if game.current_round >= bundle.clues["rounds"]:
        return "This is already the last round."
    if not _move(game, [S.LIVE], current_round=game.current_round + 1):
        return "The game changed; try again."


def open_voting(game, bundle):
    if not _move(game, [S.LIVE], status=S.VOTING):
        return "Voting can only open while the game is live."


def close_voting(game, bundle):
    if not _move(game, [S.VOTING], status=S.LIVE):
        return "Voting isn't open."


def reveal(game, bundle):
    if not _move(game, [S.VOTING], status=S.REVEALED):
        return "Open voting before the reveal."


ACTIONS = {
    "start": start,
    "next_round": next_round,
    "open_voting": open_voting,
    "close_voting": close_voting,
    "reveal": reveal,
}


def set_goal(game, player_id, met):
    if met not in (True, False, None):
        return "Say whether the goal was met."
    if not game.players.filter(pk=player_id).update(goal_met=met):
        return "No such player."


def solve(game, player, bundle, puzzle_id, submission):
    """Returns (correct, message)."""
    puzzle = next((p for p in bundle.puzzles if p["id"] == puzzle_id), None)
    if puzzle is None:
        return False, "No such puzzle."
    if game.status not in (S.LIVE, S.VOTING):
        return False, "Puzzles open when the game starts."
    if game.solves.filter(puzzle_id=puzzle_id).exists():
        return True, "Already solved."

    key = f"wrong-guesses:{player.pk}"
    if cache.get(key, 0) >= WRONG_GUESS_LIMIT:
        return False, "Too many guesses. Wait a minute and talk it through."
    if not check_answer(puzzle["answer"], submission):
        cache.add(key, 0, WRONG_GUESS_WINDOW)
        cache.incr(key)
        if puzzle["answer"]["type"] == "route":
            return False, route_hint(puzzle["answer"], submission if isinstance(submission, list) else [])
        return False, "Not quite. Keep looking."

    try:
        with transaction.atomic():
            PuzzleSolve.objects.create(game=game, puzzle_id=puzzle_id, solved_by=player)
    except IntegrityError:
        pass  # someone else got there at the same moment
    return True, "Solved!"


def vote(game, player, bundle, suspect_role_id):
    if game.status != S.VOTING:
        return "Voting isn't open."
    if suspect_role_id == player.role_id:
        return "You can't vote for yourself."
    if not game.players.filter(role_id=suspect_role_id).exists():
        return "That character isn't in this game."
    try:
        with transaction.atomic():
            Vote.objects.create(game=game, voter=player, suspect_role_id=suspect_role_id)
    except IntegrityError:
        return "You've already voted."

