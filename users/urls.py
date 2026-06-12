from django.urls import path
from . import views

urlpatterns = [
    path("/register", views.register, name="register"),
    path("/login", views.login_user, name="login"),
    path("/me", views.me_user, name="me")
]
