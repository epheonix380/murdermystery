import secrets
import uuid

from django.db import models
from django.db.models import Q


def new_token():
    return secrets.token_urlsafe(24)


class Visitor(models.Model):
    """An anonymous user, created on a first visit and remembered by a cookie."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class Game(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft"
        INVITED = "invited"
        LIVE = "live"
        VOTING = "voting"
        REVEALED = "revealed"
        ARCHIVED = "archived"

    case = models.ForeignKey("catalog.Case", on_delete=models.PROTECT, related_name="games")
    host = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="hosted_games")
    party_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.DRAFT)
    current_round = models.PositiveSmallIntegerField(default=1)
    gm_token = models.CharField(max_length=64, unique=True, default=new_token, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["host"],
                condition=~Q(status="archived"),
                name="one_active_game_per_host",
                violation_error_message="You already have an active game.",
            ),
        ]

    def __str__(self):
        return f"{self.case} ({self.get_status_display()})"


class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="players")
    display_name = models.CharField(max_length=80)
    role_id = models.CharField(max_length=40, help_text="A role id from the case's roles file")
    token = models.CharField(max_length=64, unique=True, default=new_token, editable=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game", "role_id"], name="one_player_per_role"),
        ]

    def __str__(self):
        return f"{self.display_name} as {self.role_id}"


class PuzzleSolve(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="solves")
    puzzle_id = models.CharField(max_length=40)
    solved_by = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True)
    solved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game", "puzzle_id"], name="one_solve_per_puzzle"),
        ]


class Vote(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="votes")
    suspect_role_id = models.CharField(max_length=40)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["game", "voter"], name="one_vote_per_player"),
        ]
