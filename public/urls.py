from django.urls import path
from . import views

urlpatterns = [
    path("/<str:slug_barber>/horarios", views.horarios_disponiveis),
    path("/<str:slug_barber>/agendar", views.agendar_horario),
    path("/<str:slug_barber>/barbearia", views.read_profile),
]
