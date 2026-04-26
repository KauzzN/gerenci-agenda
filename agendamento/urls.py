from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_agendamentos, name='lista'),
    path('novo/', views.criar_agendamento, name='novo'),
    path('editar/<int:id>/', views.editar_agendamento, name='editar'),
    path('excluir/<int:id>/', views.excluir_agendamento, name='excluir'),
    path('atendido/<int:id>/', views.marcar_atendido, name='atendido')
]
