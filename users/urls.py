from django.urls import path
from . import views

urlpatterns = [
    path("/usr/register", views.register, name="register"),
    path("/usr/login", views.login_user, name="login"),
    path("/usr/me", views.me_user, name="me"),
    path("/usr/update", views.update_profile, name="update"),
    path("/usr/refresh", views.refresh_session, name="refresh")
]
