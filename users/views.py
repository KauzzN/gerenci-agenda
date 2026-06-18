import json
from .decorators import jwt_required
from django.http import JsonResponse
from public.models import Profile
from django.contrib.auth.models import User
from .services.auth_services import generate_tokens
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout

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