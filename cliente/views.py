from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from users.decorators import jwt_required
from django.contrib.auth.models import User
from .services import validar_cliente, validar_telefone
from agendamento.utils.agendamento_utils import parse_json_body
from .models import Cliente, ClienteProfissional
from public.models import Profile
from users.services.token_services import generate_tokens

# Create your views here.

@csrf_exempt
def cliente_entry(request, slug_barber):

    # Checa método http
    if request.method != "POST":

        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    # Busca profissional pelo Slug
    try:

        profile = Profile.objects.get(
            public_slug=slug_barber
        )

    except Profile.DoesNotExist:

        return JsonResponse({
            "detail": "profissional não encontrado"
        }, status=404)
    
    # Lê o json enviado
    data, error = parse_json_body(request)

    if error:

        return JsonResponse({
            "detail": str(error)
        }, status=400)

    cliente, erro = validar_cliente(data)

    if erro:

        return JsonResponse({
            "detail": str(erro)
        })


    if cliente is None:

        telefone = data["telefone"]
        nome = data["nome"]
        telefone, error = validar_telefone(telefone)

        if error: 
            return JsonResponse({
                "detail": str(error)
            }, status=400)
        

        # Cria usuario
        user = User.objects.create(
                    username=telefone
                )

        user.set_unusable_password()
        user.save()

        # Cria cliente
        cliente = Cliente.objects.create(
            user=user,
            telefone=telefone,
            nome=nome
        )
    

    else:

        user = cliente.user
    
    # Cria relação cliente profissional
    cliente_profissional, created = ClienteProfissional.objects.get_or_create(
        cliente=cliente,
        profile=profile
    )

    tokens = generate_tokens(user)

    return JsonResponse({
    "message": "cliente autenticado",
    "cliente": {
        "user": user.id,
        "nome": cliente.nome,
        "telefone": cliente.telefone,
        "profissional": profile.nome_negocio
    },
    "tokens": tokens
}, status=201)

@jwt_required
@csrf_exempt
def read_own_profile(request):

    if request.method != "GET":
        return JsonResponse({
            "erro": "método não permitido"
        }, status=405)

    data, error = parse_json_body(request)

    if error:
        return JsonResponse({
            "detail": str(error)
        }, status=400)

    cliente, error = validar_cliente(data)

    user = cliente.user

    return JsonResponse({
        "cliente": {
            "id": user.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
        }
    })

@jwt_required
@csrf_exempt
def read_profile_clients(request):

    if request.method != "GET":

        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    user = request.user

    try:
        profile = Profile.objects.get(
            user=user
        )

    except Profile.DoesNotExist:

        return JsonResponse({
            "error": "profissional não encontrado"
        }, satus=404)

    clientes = Cliente.objects.filter(
        relacoes_profissionais__profile=profile
    )

    lista_clientes = []

    for cliente in clientes:

        user = cliente.user

        cliente_iterado = {
            "id": user.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
        }

        lista_clientes.append(cliente_iterado)

    return JsonResponse({
        "clientes": lista_clientes
    }, status=200)