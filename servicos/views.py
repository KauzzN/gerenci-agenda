from django.shortcuts import render
from users.decorators import jwt_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from servicos.models import Servico
from django.http import JsonResponse
from agendamento.utils.agendamento_utils import parse_json_body
from servicos.services import atualizar_servico


# Create your views here.
@jwt_required
@csrf_exempt
def create_service(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    data, error = parse_json_body(request)

    if error:
        return JsonResponse({
            "detail": str(error)
        }, status=400)

    nome = data.get("nome")
    preco = data.get("preco")
    duracao = data.get("duracao")
    descricao = data.get("descricao")
    cor = data.get("cor")

    duplicidade = Servico.objects.filter(
        user=user,
        nome=nome
    ).exists()

    if duplicidade:
        return JsonResponse({
            "error": "este serviço já existe"
        }, status=400)

    servico = Servico.objects.create(
        user=user,
        nome=nome,
        preco=preco,
        duracao=duracao,
        descricao=descricao,
        cor=cor
    )

    return JsonResponse({
        "message": "servico criado com sucesso!",
        "servico": {
            "nome": servico.nome,
            "preco": servico.preco,
            "duracao": servico.duracao,
            "descricao": servico.descricao,
            "ativo": servico.ativo,
            "cor": servico.cor
        }
    }, status=201)

@jwt_required
@csrf_exempt
def read_all_services(request):

    if request.method != "GET":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    servicos = Servico.objects.filter(
        user=user
    )

    lista_servicos = []

    for servico in servicos:
        servico_iterado = {
            "nome": servico.nome,
            "preco": servico.preco,
            "duracao": servico.duracao,
            "descricao": servico.descricao,
            "cor": servico.cor,
            "ativo": servico.ativo
        }

        lista_servicos.append(servico_iterado)

    return JsonResponse({
        "serviços": lista_servicos
    }, status=200)

@jwt_required
@csrf_exempt
def read_one_service(request, service_id):

    if request.method != "GET":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    servico = Servico.objects.get(
        user=user,
        id=service_id
    )

    return JsonResponse({
        "servico": {
            "nome": servico.nome,
            "preço": servico.preco,
            "duracão": servico.duracao,
            "descrição": servico.descricao,
            "cor": servico.cor,
            "ativo": servico.ativo
        }
    })

@jwt_required
@csrf_exempt
def update_service(request, service_id):

    if request.method != "PATCH":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    try:
        servico = Servico.objects.get(
            user=user,
            id=service_id
        )

    except Servico.DoesNotExist:
        return JsonResponse({
            "error": "serviço não encontrado"
        }, status=404)

    data, error = parse_json_body(request)

    if error:
        return JsonResponse({
            "detail": str(error)
        }, status=400)

    updated, error =  atualizar_servico(request, servico, data)

    if error:
        return JsonResponse({
            "detail": str(error)
        }, status=400)

    if not updated:
        return JsonResponse({
            "message": "nenhuma alteração realizada"
        }, status=200)

    return JsonResponse({
        "message": "serviço atualizado",
        "serviço": {
            "nome": servico.nome,
            "preco": servico.preco,
            "duracao": servico.duracao,
            "descricao": servico.descricao,
            "cor": servico.cor,
            "ativo": servico.ativo
        }
    })

@jwt_required
@csrf_exempt
def delete_service(request, service_id):

    if request.method != "DELETE":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    try:
        servico = Servico.objects.get(
            user=user,
            id=service_id
        )

    except Servico.DoesNotExist:
        return JsonResponse({
            "error": "serviço não encontrado"
        }, status=404)

    Servico.delete(servico)

    return JsonResponse({
        "message": "serviço deletado com sucesso"
    }, status=200)
