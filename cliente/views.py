from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from users.decorators import jwt_required
from django.contrib.auth.models import User
from .services import validar_cliente
from agendamento.utils.agendamento_utils import parse_json_body
from .models import Cliente, ClienteProfissional
from public.models import Profile
from users.services.token_services import generate_tokens

# Create your views here.

@csrf_exempt
def create_cliente(request, slug_barber):

    # Checa método http
    if request.method != "POST":

        return JsonResponse({
            "error": "metodo não permitido"
        }, status=405)

    # Busca profissional pelo Slug
    try:

        profile = Profile.objects.get(
            public_slug=slug_barber
        )

    except Profile.DoesNotExist:

        return JsonResponse({
            "detail": "profissional não encontra"
        }, status=404)

    # Lê o json enviado
    data, error = parse_json_body(request)

    if error:

        return JsonResponse({
            "detail": str(error)
        }, status=400)

    # Pegao os dados do cliente
    nome = data.get("nome")
    telefone = data.get("telefone").strip()

    # Valida os campos obrigatórios
    if not nome or not telefone:

        return JsonResponse({
            "detail": "nome e telefone sao obrigatorios"
        }, status=400)

    # Procura cliente pelo telefone
    cliente = Cliente.objects.filter(
        telefone=telefone
    ).first()

    # Se o cliente não existir, cria um
    if cliente is None:

        user = User.objects.create(
            username=telefone
        )

        user.set_unusable_password()
        user.save()

        cliente = Cliente.objects.create(
            user=user,
            telefone=telefone,
            nome=nome
        )

    # Cria relação cliente profissional
    cliente_profissional, created = ClienteProfissional.objects.get_or_create(
        cliente=cliente,
        profile=profile
    )

    user = User.objects.get(cliente=cliente)

    tokens = generate_tokens(user)

    print(tokens)


    return JsonResponse({
        "cliente": {
            "id": cliente.id,
            "nome": cliente.nome,
            "telefone": cliente.telefone
        },
        "tokens": tokens
    }, status=201)

@csrf_exempt
def login_cliente(request): 

    if request.method != "POST":

        return JsonResponse({
            "error": "método não permitido"
        }, status=405)

    data, error = parse_json_body(request)

    if error:
        return JsonResponse({
            "detail": str(error)
        })

    cliente, error = validar_cliente(data)

    if error:
        return JsonResponse({
            "detail": str(error)
        })

    user = User.objects.get(cliente=cliente)

    tokens = generate_tokens(user)

    return JsonResponse({
        "message": "login concluido",
        "tokens": tokens
    })

@csrf_exempt
def read_own_profile(request, slug_barber):

    if request.method != "GET":
        return JsonResponse({
            "erro": "método não permitido"
        }, status=405)

    data, error = parse_json_body(request)

    if error:
        return JsonResponse({
            "detail": str(error)
        }, status=400)

    cliente, error = validar_cliente(slug_barber, data)

    return JsonResponse({
        "cliente": {
            "nome": cliente
        }
    })