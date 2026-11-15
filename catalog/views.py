from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404

from .models import Case


def public_file(request, slug, path):
    """Serve a file from a case's public/ folder (its map, for example).

    Only public/ is reachable, so the JSON files beside it, which hold every
    secret in the case, can never be downloaded.
    """
    case = get_object_or_404(Case, slug=slug)
    public = (settings.CASES_DIR / case.folder / "public").resolve()
    target = (public / path).resolve()
    if not target.is_relative_to(public) or not target.is_file():
        raise Http404
    return FileResponse(open(target, "rb"))
