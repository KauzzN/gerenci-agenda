import jwt
import uuid
import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


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