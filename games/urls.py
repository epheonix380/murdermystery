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
    path("host/state/", views.host_state, name="host-state"),
    path("host/action/", views.host_action, name="host-action"),
    path("host/goal/", views.host_goal, name="host-goal"),
    path("host/print/", views.host_print, name="host-print"),
    path("p/<str:token>/", views.player_sheet, name="player"),
    path("p/<str:token>/state/", views.player_state, name="player-state"),
    path("p/<str:token>/solve/", views.player_solve, name="player-solve"),
    path("p/<str:token>/vote/", views.player_vote, name="player-vote"),
]
