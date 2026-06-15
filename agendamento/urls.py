from django.urls import path
from . import views

urlpatterns = [
    path('/read', views.listar_agendamentos, name='read'),
    path('/create', views.criar_agendamento, name='create'),
    path('/update/<int:id_agend>', views.update_agendamentos, name='update')
]
