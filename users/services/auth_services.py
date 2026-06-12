import secrets
from .token_services import generate_access_token, decode_access_token


def generate_tokens(user):
    
    access_token = generate_access_token(user)
    
    return {
        "access_token": access_token
    }
    
