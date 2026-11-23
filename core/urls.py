from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("partite/", views.fixture_list, name="fixture_list"),
    path("partite/<int:pk>/", views.fixture_detail, name="fixture_detail"),
    path("partite/<int:pk>/modifica/", views.fixture_edit, name="fixture_edit"),
    path("partite/<int:pk>/elimina/", views.fixture_delete, name="fixture_delete"),
    path("referto/", views.report_upload, name="report_upload"),
]
