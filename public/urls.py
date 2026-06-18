from django.urls import path
from . import views

urlpatterns = [
    path("/<str:slug_barber>/horarios", views.horarios_disponiveis)
]
