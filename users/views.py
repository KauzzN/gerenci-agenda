import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

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
    
    return JsonResponse({
        "message": "usuario criado com sucesso"
    }, status=201)
    
@csrf_exempt
def login(request):
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
        
    return JsonResponse({
        "message": "autenticação concluida"
    }, status=200)
        
        
        
        
    
    