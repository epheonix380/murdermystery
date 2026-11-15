from django.urls import re_path

from .consumers import GameConsumer

websocket_urlpatterns = [
    re_path(r"^ws/(?P<kind>p|gm)/(?P<token>[\w-]+)/$", GameConsumer.as_asgi()),
]
