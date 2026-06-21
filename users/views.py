import json
from .decorators import jwt_required
from django.http import JsonResponse
from public.models import Profile
from django.contrib.auth.models import User
from .services.auth_services import generate_tokens
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
    
    return JsonResponse({
        "message": "usuario criado com sucesso"
    }, status=201)
    
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
        "tokens": {
            "access_token": tokens["access_token"]
        }
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
        
    updated = atualizar_profile(profile, data)
    
    if not updated:
        return JsonResponse({
            "message": "nenhuma alteração realizada"
        }, status=200)
        
    # Retornar sucesso
    return JsonResponse({
        "message": "profile atualizada",
        "profile": {
            "slug": profile.public_slug,
            "nome_negocio": profile.nome_negocio,
            "telefone": profile.telefone
        }
    })