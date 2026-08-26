from django.urls import path
from . import views

urlpatterns = [
    path("/cli/teste/<str:slug_barber>", views.cliente_entry),
    path("/cli/read", views.read_own_profile),
    path("/cli/read/clients", views.read_profile_clients)
]
