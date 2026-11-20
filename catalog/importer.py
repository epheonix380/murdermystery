from django.conf import settings
from django.db import transaction

from .loader import load_case
from .models import Case


@transaction.atomic
def import_case(folder, published=None):
    """Check a case folder and create or refresh its Case row.

    `published` None keeps an existing row's setting; a new case starts
    published unless told otherwise. Raises CaseError if the folder has
    problems, leaving the database untouched.
    """
    bundle = load_case(folder)
    m = bundle.manifest
    files = m["files"]
    folder = bundle.folder.resolve()
    cases_dir = settings.CASES_DIR.resolve()
    # Stored relative to CASES_DIR when inside it, so the database survives the folder moving.
    folder_rel = folder.relative_to(cases_dir) if folder.is_relative_to(cases_dir) else folder

    case = Case.objects.filter(slug=bundle.slug).first() or Case(slug=bundle.slug, published=True)
    if published is not None:
        case.published = published
    case.title = m["title"]
    case.premise = m["premise"]
    case.rules = m["rules"]
    case.min_players = m["min_players"]
    case.max_players = m["max_players"]
    case.map_url = bundle.map_url
    case.clue_count = bundle.clue_count
    case.puzzle_count = len(bundle.puzzles)
    case.prop_count = len(bundle.props)
    case.folder = str(folder_rel)
    case.roles_file = str(folder_rel / files["roles"])
    case.clues_file = str(folder_rel / files["clues"])
    case.puzzles_file = str(folder_rel / files["puzzles"])
    case.props_file = str(folder_rel / files["props"])
    case.solution_file = str(folder_rel / files["solution"])
    case.extras_file = str(folder_rel / files["extras"]) if "extras" in files else ""
    case.save()
    return case
