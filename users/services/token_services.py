import jwt
import uuid
import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from users.models import RefreshToken

# Access Token
def generate_access_token(user):
    
    now = timezone.now()
    
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
        "jti": str(uuid.uuid4())
    }
    
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    
    return token

def decode_access_token(token):
    
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"]
    )
    
    return payload


# Refresh Tokens
def generate_tokens(user):

    access_token = generate_access_token(user)

    refresh_token = secrets.token_urlsafe(64)

    create_refresh_token(user, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

def create_refresh_token(user, raw_token):
    
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    expires_at = timezone.now() + timedelta(days=7)
    
    RefreshToken.objects.filter(
        user=user, revoked=False
    ).update(
        revoked=True
    )
    
    refresh_token = RefreshToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=expires_at
    )
    
    return refresh_token
    
def validate_refresh_token(raw_token):
    
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    try:
        refresh_token = RefreshToken.objects.get(token_hash=token_hash)
        
    except RefreshToken.DoesNotExist:
        return None, "token inválido"
    
    if refresh_token.revoked:
        return None, "refresh token revogado"
    
    if refresh_token.is_expired():
        refresh_token.revoked = True
        refresh_token.save()
        
        return None, "refresh token expirado"
    
    return refresh_token, None
    
def revoke_token(token):
    
    token.revoked = True
    token.save()
    
def delete_token(token):
    
    token.delete()