from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name="profile"
    )
    
    nome_negocio = models.CharField(max_length=100)
    
    public_slug = models.SlugField(
        unique=True,
        max_length=100
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    updated_at = models.DateTimeField(auto_now=True)