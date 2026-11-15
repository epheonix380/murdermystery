import json
from functools import wraps

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalog.loader import bundle_for
from catalog.models import Case

from . import engine
from .casting import CastingError, cast_roles
from .live import notify
from .forms import NewGameForm
from .models import Game, Player
from .visitor import current_visitor, remember


def home(request):
    Game.archive_stale()
    return render(request, "games/home.html", {
        "cases": Case.objects.filter(published=True),
        "active_game": Game.active_for(current_visitor(request)),
    })


def new_game(request, slug):
    case = get_object_or_404(Case, slug=slug, published=True)
    if Game.active_for(current_visitor(request)):
        messages.info(request, "You already have an active game. End it before starting another.")
        return redirect("host")

    form = NewGameForm(case, request.POST or None)
    if request.method == "POST" and form.is_valid():
        visitor = current_visitor(request, create=True)
        try:
            with transaction.atomic():
                Game.objects.create(case=case, host=visitor, **form.cleaned_data)
        except IntegrityError:
            # Another tab created a game first.
            messages.info(request, "You already have an active game.")
            return redirect("host")
        return redirect("host-players")
    return render(request, "games/new_game.html", {"case": case, "bundle": bundle_for(case), "form": form})


def host_only(view):
    """Pass the visitor's active game to the view, or send them home."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        game = Game.active_for(current_visitor(request))
        if game is None:
            messages.info(request, "You don't have an active game. Pick a case to host one.")
            return redirect("home")
        return view(request, game, *args, **kwargs)

    return wrapper


def _role_names(bundle):
    return {r["id"]: r["name"] for r in bundle.roles}


@host_only
def host_dashboard(request, game):
    bundle = bundle_for(game.case)
    rooms = {r["id"]: r["name"] for r in bundle.extras.get("map", {}).get("rooms", [])}
    return render(request, "games/host_dashboard.html", {
        "game": game,
        "bundle": bundle,
        "has_players": game.players.exists(),
        "answers": [(p, _readable_answer(p["answer"], rooms)) for p in bundle.puzzles],
        "notes": {k: v for k, v in bundle.extras.items() if isinstance(v, str) and k not in _shown_elsewhere(bundle)},
        "gm_url": request.build_absolute_uri(reverse("gm-link", args=[game.gm_token])),
        "cfg": {
            "stateUrl": reverse("host-state"),
            "actionUrl": reverse("host-action"),
            "goalUrl": reverse("host-goal"),
            "wsPath": f"/ws/gm/{game.gm_token}/",
        },
    })


def _readable_answer(answer, rooms):
    if answer["type"] == "route":
        return " → ".join(rooms.get(r, r) for r in [answer["start"], *answer["sequence"]])
    return " or ".join(answer["accept"])


def _shown_elsewhere(bundle):
    """Extras fields that puzzles or clue cards already show players."""
    used = {p["shows"] for p in bundle.puzzles if "shows" in p}
    return used | {c["shows"] for c in bundle.clues.get("cards", []) if "shows" in c}


@host_only
def host_players(request, game):
    if not game.can_edit_cast:
        messages.info(request, "The game has started, so the cast can't change.")
        return redirect("host")
    bundle = bundle_for(game.case)
    case = game.case
    existing = list(game.players.order_by("id"))

    source = request.POST if request.method == "POST" else request.GET
    try:
        count = int(source.get("count", ""))
    except ValueError:
        count = len(existing) or game.player_count
    count = min(max(count, case.min_players), case.max_players)

    if request.method == "POST":
        rows = [(request.POST.get(f"name_{i}", ""), request.POST.get(f"role_{i}", "")) for i in range(count)]
        player_ids = [request.POST.get(f"player_{i}", "") for i in range(count)]
        try:
            cast = cast_roles(bundle.roles, case.min_players, case.max_players, rows)
        except CastingError as e:
            for problem in e.problems:
                messages.error(request, problem)
        else:
            _save_cast(game, existing, player_ids, cast)
            messages.success(request, "Cast saved. Send each player their link.")
            return redirect("host-links")
    else:
        rows = [(p.display_name, p.role_id) for p in existing]
        player_ids = [str(p.pk) for p in existing]

    rows = (rows + [("", "")] * count)[:count]
    player_ids = (player_ids + [""] * count)[:count]
    return render(request, "games/host_players.html", {
        "game": game,
        "bundle": bundle,
        "count": count,
        "counts": range(case.min_players, case.max_players + 1),
        "rows": [(i, name, role_id, pid) for i, ((name, role_id), pid) in enumerate(zip(rows, player_ids))],
        "has_players": bool(existing),
    })


@transaction.atomic
def _save_cast(game, existing, player_ids, cast):
    """Save the cast, keeping each existing player's link so links already sent still work."""
    by_id = {str(p.pk): p for p in existing}
    kept = {pid for pid in player_ids if pid in by_id}
    Player.objects.filter(pk__in=[p.pk for p in existing if str(p.pk) not in kept]).delete()
    # Clear roles first so swapping two players' roles can't trip the one-player-per-role rule.
    for pid in kept:
        Player.objects.filter(pk=by_id[pid].pk).update(role_id=f"__swap{pid}")
    for pid, (name, role_id) in zip(player_ids, cast):
        if pid in kept:
            Player.objects.filter(pk=by_id[pid].pk).update(display_name=name, role_id=role_id)
        else:
            Player.objects.create(game=game, display_name=name, role_id=role_id)
    game.player_count = len(cast)
    game.status = Game.Status.INVITED
    game.save(update_fields=["player_count", "status"])


@host_only
def host_links(request, game):
    names = _role_names(bundle_for(game.case))
    links = [
        (p.display_name, names.get(p.role_id, p.role_id), request.build_absolute_uri(reverse("player", args=[p.token])))
        for p in game.players.order_by("id")
    ]
    return render(request, "games/host_links.html", {
        "game": game,
        "links": links,
        "gm_url": request.build_absolute_uri(reverse("gm-link", args=[game.gm_token])),
    })


@require_POST
@host_only
def host_end(request, game):
    game.status = Game.Status.ARCHIVED
    game.save(update_fields=["status"])
    messages.success(request, "Game ended. You can host another one now.")
    return redirect("home")


def gm_link(request, token):
    """The GM's private link: makes this browser the game's host, on any device."""
    game = get_object_or_404(Game.objects.exclude(status=Game.Status.ARCHIVED), gm_token=token)
    remember(request, game.host)
    return redirect("host")


def player_sheet(request, token):
    player = get_object_or_404(Player.objects.select_related("game__case"), token=token)
    game = player.game
    Player.objects.filter(pk=player.pk).update(last_seen=timezone.now())
    bundle = bundle_for(game.case)
    role = bundle.role(player.role_id)
    if role is None:
        raise Http404
    roles = {r["id"]: r for r in bundle.roles}
    cast = [
        {"player": p.display_name, "name": roles[p.role_id]["name"], "costume": roles[p.role_id]["costume"],
         "who": roles[p.role_id]["who"], "is_you": p.pk == player.pk}
        for p in game.players.order_by("id") if p.role_id in roles
    ]
    return render(request, "games/player_sheet.html", {
        "player": player,
        "game": game,
        "case": game.case,
        "victim": bundle.manifest.get("victim"),
        "role": role,
        "is_killer": role["id"] == bundle.solution["killer"],
        "cast": cast,
        "ended": game.status == Game.Status.ARCHIVED,
        "cfg": {
            "stateUrl": reverse("player-state", args=[token]),
            "solveUrl": reverse("player-solve", args=[token]),
            "voteUrl": reverse("player-vote", args=[token]),
            "wsPath": f"/ws/p/{token}/",
            "map": bundle.extras.get("map"),
            "bodyViewer": bundle.body_viewer_url,
        },
    })

# ---------- game night (JSON) ----------

def _json_body(request):
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _player_or_404(token):
    player = get_object_or_404(Player.objects.select_related("game__case"), token=token)
    if player.game.status == Game.Status.ARCHIVED:
        raise Http404
    return player


def player_state(request, token):
    player = _player_or_404(token)
    return JsonResponse(engine.player_state(player.game, player, bundle_for(player.game.case)))


@require_POST
def player_solve(request, token):
    player = _player_or_404(token)
    data = _json_body(request)
    correct, message = engine.solve(
        player.game, player, bundle_for(player.game.case), str(data.get("puzzle", "")), data.get("answer", "")
    )
    if correct:
        notify(player.game)
    return JsonResponse({"correct": correct, "message": message})


@require_POST
def player_vote(request, token):
    player = _player_or_404(token)
    error = engine.vote(player.game, player, bundle_for(player.game.case), str(_json_body(request).get("suspect", "")))
    if error:
        return JsonResponse({"error": error}, status=400)
    notify(player.game)
    return JsonResponse({"ok": True})


@host_only
def host_state(request, game):
    return JsonResponse(engine.gm_state(game, bundle_for(game.case)))


@require_POST
@host_only
def host_action(request, game):
    action = engine.ACTIONS.get(str(_json_body(request).get("action", "")))
    if action is None:
        return JsonResponse({"error": "Unknown action."}, status=400)
    error = action(game, bundle_for(game.case))
    if error:
        return JsonResponse({"error": error}, status=400)
    notify(game)
    return JsonResponse({"ok": True})


@require_POST
@host_only
def host_goal(request, game):
    data = _json_body(request)
    error = engine.set_goal(game, data.get("player"), data.get("met"))
    if error:
        return JsonResponse({"error": error}, status=400)
    notify(game)
    return JsonResponse({"ok": True})


@host_only
def host_print(request, game):
    bundle = bundle_for(game.case)
    cast = set(game.players.values_list("role_id", flat=True))
    kind = request.GET.get("kind", "cards")
    cards = [c for c in bundle.clues.get("cards", []) if c.get("requires_role", None) in (None, *cast)]
    item_clues = {p["clue"] for p in bundle.props if "clue" in p}
    return render(request, "games/print.html", {
        "game": game,
        "kind": "labels" if kind == "labels" else "cards",
        "cards": cards,
        "item_clues": item_clues,
        "extras": bundle.extras,
        "search_locations": bundle.search_locations,
        "sealed": bundle.clues.get("sealed", []),
    })
