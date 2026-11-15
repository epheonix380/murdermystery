"""Anonymous visitors, remembered by a cookie instead of an account."""

import uuid

from django.conf import settings

from .models import Visitor

COOKIE = "mm_visitor"
COOKIE_AGE = 60 * 60 * 24 * 365


def current_visitor(request, create=False):
    """The Visitor behind this request's cookie, or None.

    With create=True a new Visitor is made when there is none; the middleware
    then sends its cookie. Visitors are only created when someone starts to
    host, so crawlers and players don't fill the table.
    """
    if getattr(request, "_visitor", None) is None:
        request._visitor = None
        raw = request.COOKIES.get(COOKIE)
        if raw:
            try:
                request._visitor = Visitor.objects.filter(pk=uuid.UUID(raw)).first()
            except ValueError:
                pass
    if request._visitor is None and create:
        remember(request, Visitor.objects.create())
    return request._visitor


def remember(request, visitor):
    """Make this browser act as `visitor` from now on."""
    request._visitor = visitor
    request._set_visitor_cookie = True


class VisitorCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "_set_visitor_cookie", False):
            response.set_cookie(
                COOKIE,
                str(request._visitor.pk),
                max_age=COOKIE_AGE,
                httponly=True,
                samesite="Lax",
                secure=not settings.DEBUG,
            )
        return response
