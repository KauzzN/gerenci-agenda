from django.urls import path
from . import views

urlpatterns = [
    path("/serv/create", views.create_service),
    path("/serv/read", views.read_all_services),
    path("/serv/read/<int:service_id>", views.read_one_service),
    path("/serv/update/<int:service_id>", views.update_service),
    path("/serv/delete/<int:service_id>", views.delete_service)
]
