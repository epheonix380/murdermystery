from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("host/new/<slug:slug>/", views.new_game, name="new-game"),
    path("host/", views.host_dashboard, name="host"),
    path("host/players/", views.host_players, name="host-players"),
    path("host/links/", views.host_links, name="host-links"),
    path("host/end/", views.host_end, name="host-end"),
    path("gm/<str:token>/", views.gm_link, name="gm-link"),
    path("p/<str:token>/", views.player_sheet, name="player"),
]
