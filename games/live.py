"""Telling everyone in a game that something changed.

Phones keep a WebSocket open to /ws/<kind>/<token>/. When a game changes,
each one gets a bare "changed" message and fetches its own state again over
HTTP, so the rules about who sees what live in one place (engine.py).
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


def group_name(game_id):
    return f"game-{game_id}"


def notify(game):
    def send():
        layer = get_channel_layer()
        if layer is not None:
            async_to_sync(layer.group_send)(group_name(game.pk), {"type": "game.changed"})

    transaction.on_commit(send)
