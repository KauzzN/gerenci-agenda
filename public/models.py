from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    
    nome_negocio = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    telefone = models.CharField(max_length=15, blank=True)
    public_slug = models.SlugField(
        unique=True,
        max_length=100,
        blank=True,
        null=True
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="profile")