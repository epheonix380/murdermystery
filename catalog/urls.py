from django.urls import path

from . import views

urlpatterns = [
    path("cases/<slug:slug>/public/<path:path>", views.public_file, name="case-public-file"),
]
