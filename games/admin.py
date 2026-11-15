from django.contrib import admin

from .models import Game, Player, PuzzleSolve, Visitor, Vote


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    readonly_fields = ["token", "last_seen"]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ["case", "status", "party_date", "current_round", "host", "created_at"]
    list_filter = ["status", "case"]
    readonly_fields = ["gm_token", "created_at"]
    inlines = [PlayerInline]


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ["id", "created_at", "last_seen"]


admin.site.register(PuzzleSolve)
admin.site.register(Vote)
