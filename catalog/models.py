from django.db import models


class Case(models.Model):
    """One mystery, as listed in the case browser.

    The case folder is the source of truth: this row holds what the browser
    shows plus the paths to the case's JSON files, and is refreshed from the
    folder by `manage.py import_case`.
    """

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    premise = models.JSONField(default=list)
    rules = models.JSONField(default=list)
    min_players = models.PositiveSmallIntegerField()
    max_players = models.PositiveSmallIntegerField()
    map_url = models.CharField(max_length=500, blank=True)

    clue_count = models.PositiveIntegerField(default=0)
    puzzle_count = models.PositiveIntegerField(default=0)
    prop_count = models.PositiveIntegerField(default=0)

    published = models.BooleanField(default=False)

    # Paths relative to CASES_DIR. Never served to browsers.
    folder = models.CharField(max_length=200)
    roles_file = models.CharField(max_length=300)
    clues_file = models.CharField(max_length=300)
    puzzles_file = models.CharField(max_length=300)
    props_file = models.CharField(max_length=300)
    solution_file = models.CharField(max_length=300)
    extras_file = models.CharField(max_length=300, blank=True)

    imported_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
