from django.urls import path
from . import views

urlpatterns = [
    path('/agendar/read', views.listar_agendamentos, name='read'),
    path('/agendar/create', views.criar_agendamento, name='create'),
    path('/agendar/update/<int:id_agend>', views.update_agendamentos, name='update'),
    path('/agendar/delete/<int:id_agend>', views.delete_agendamento, name='delete'),
    path('/agendar/status/<int:id_agend>', views.atualizar_status, name='status')
]
