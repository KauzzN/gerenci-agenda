import json
import hashlib
from .decorators import jwt_required
from django.http import JsonResponse
from public.models import Profile
from users.models import RefreshToken
from django.contrib.auth.models import User
from .services.token_services import validate_refresh_token, generate_tokens
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from agendamento.utils.agendamento_utils import parse_json_body
from public.services.public_services import atualizar_profile

# Create your views here.

@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
    
    data = json.loads(request.body.decode("utf-8"))
    
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if User.objects.filter(username=username).exists():
        return JsonResponse({
            "error": "username já existe"
        }, status=400)
        
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    
    Profile.objects.create(user=user)
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return JsonResponse({
            "error": "usuario não encontrado"
        }, status=404)
        
    tokens = generate_tokens(user)
        
    return JsonResponse({
        "message": "usuário criado com sucesso",
        "tokens": tokens
    }, status=200)
    
@csrf_exempt
def login_user(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
        
    data = json.loads(request.body.decode("utf-8"))
    
    username = data.get("username")
    
    if not username:
        return JsonResponse({
            "error": "usuario inválido"
        }, status=401)
        
    password = data.get("password")
    
    if not password:
        return JsonResponse({
            "error": "password inválido"
        }, status=401)
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return JsonResponse({
            "error": "usuario não encontrado"
        }, status=404)
        
    tokens = generate_tokens(user)
        
    return JsonResponse({
        "message": "autenticação concluida",
        "tokens": tokens
    }, status=200)
    
@csrf_exempt
@jwt_required
def me_user(request): 
    if request.method != "GET":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
    
    user = request.user
    
    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })
    
@csrf_exempt
@jwt_required
def update_profile(request):
    if request.method != "PATCH":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)
        
    print("entrou na view")
    
    # Buscar e validar Profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return JsonResponse({
            "error": "barbearia não encontrada"
        }, status=404)
        
    # Atualizar dados do Profile
    data, error = parse_json_body(request)
    
    if error:
        return JsonResponse({
            "error": error
        }, status=400)
        
    updated, error = atualizar_profile(profile, data)
    
    if error:
        return JsonResponse({
            "error": error
        }, status=400)
    
    if not updated:
        return JsonResponse({
            "message": "nenhuma alteração realizada"
        }, status=200)
        
    # Retornar sucesso
    return JsonResponse({
        "message": "profile atualizada",
        "profile": {
            "user": str(profile.user),
            "public_slug": profile.public_slug,
            "nome_negocio": profile.nome_negocio,
            "telefone": profile.telefone
        }
    })
    
@csrf_exempt
def refresh_session(request):
    
    if request.method != "POST":
        return JsonResponse({
            "error": "método não permitido"
        }, status=405)
        
    data, error = parse_json_body(request)
    
    if error:
        return JsonResponse({
            "error": error
        }, status=400)
    
    token = data.get("refresh_token")
    
    if not token:
        return JsonResponse({
            "error": "refresh_token não inserido"
        }, status=400)
        
    refresh_token, error = validate_refresh_token(token)
    
    if error:
        return JsonResponse({
            "error": error
        }, status=400)
        
    if refresh_token.user is None:
        refresh_token.revoked = True
        
        return JsonResponse({
            "error": "refresh_token inválido"
        }, status=400)
    
    user = refresh_token.user
    
    return JsonResponse(generate_tokens(user))
        

@csrf_exempt
@jwt_required
def meu_profile(request):
    
    profile = request.user.profile
    
    return JsonResponse({
        "public_slug": profile.public_slug,
        "nome_negocio": profile.nome_negocio,
        "telefone": profile.telefone
    })