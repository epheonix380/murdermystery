from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .live import group_name
from .models import Game, Player


@database_sync_to_async
def _game_id(kind, token):
    if kind == "p":
        player = Player.objects.filter(token=token).exclude(game__status=Game.Status.ARCHIVED).first()
        return player.game_id if player else None
    game = Game.objects.filter(gm_token=token).exclude(status=Game.Status.ARCHIVED).first()
    return game.pk if game else None


class GameConsumer(AsyncJsonWebsocketConsumer):
    """Pings a phone whenever its game changes. Carries no game data itself."""

    async def connect(self):
        kwargs = self.scope["url_route"]["kwargs"]
        game_id = await _game_id(kwargs["kind"], kwargs["token"])
        if game_id is None:
            await self.close(code=4404)
            return
        self.group = group_name(game_id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def game_changed(self, event):
        await self.send_json({"type": "changed"})
