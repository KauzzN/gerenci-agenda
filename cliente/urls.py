from django.urls import path
from .views import create_cliente, login_cliente

urlpatterns = [
    path("/cli/create/<str:slug_barber>", create_cliente),
    path("/cli/signin", login_cliente)
]
