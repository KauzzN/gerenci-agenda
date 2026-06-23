from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class RefreshToken(models.Model):
    
    user =  models.ForeignKey(User, on_delete=models.CASCADE)
    
    token_hash = models.CharField(max_length=64, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    expires_at = models.DateTimeField()
    
    revoked = models.BooleanField(default=False)
    
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    
    def is_expired(self):
        
        return timezone.now() >= self.expires_at