from django.contrib import admin

from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ["title", "published", "min_players", "max_players", "clue_count", "puzzle_count", "prop_count", "imported_at"]
    list_filter = ["published"]
    list_editable = ["published"]
    # Everything except `published` comes from the case folder; edit the files
    # and run `manage.py import_case` instead.
    readonly_fields = [
        "slug", "title", "premise", "rules", "min_players", "max_players", "map_url",
        "clue_count", "puzzle_count", "prop_count", "folder", "roles_file", "clues_file",
        "puzzles_file", "props_file", "solution_file", "extras_file", "imported_at",
    ]

    def has_add_permission(self, request):
        return False
