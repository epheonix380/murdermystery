from django.db import connection
from django.http import HttpResponse


def healthz(request):
    """For Docker's healthcheck: the app is up and can reach the database."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")
