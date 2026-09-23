from users.decorators import professional_required
from servicos.models import Servico
from django.http import JsonResponse
from decimal import Decimal, InvalidOperation
from agendamento.utils.agendamento_utils import parse_json_body
from servicos.services import atualizar_servico


@professional_required
def create_service(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    data, error = parse_json_body(request)
    if error:
        return error

    nome = data.get("nome")
    preco = data.get("preco")
    duracao = data.get("duracao")
    descricao = data.get("descricao")
    cor = data.get("cor")

    if not nome:
        return JsonResponse({
            "error": "nome do serviço é obrigatório"
        }, status=400)

    try:
        preco = Decimal(str(preco))
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({
            "error": "preço deve ser um número válido"
        }, status=400)

    if preco < 0:
        return JsonResponse({
            "error": "preço não pode ser negativo"
        }, status=400)

    if isinstance(duracao, bool) or not isinstance(duracao, int) or duracao <= 0:
        return JsonResponse({
            "error": "duração deve ser um número inteiro maior que zero"
        }, status=400)

    if descricao is not None and (
        not isinstance(descricao, str) or len(descricao) > 200
    ):
        return JsonResponse({
            "error": "descrição inválida"
        }, status=400)

    if cor is not None and (
        not isinstance(cor, str)
        or len(cor) not in (4, 7)
        or not cor.startswith("#")
        or any(
            character not in "0123456789abcdefABCDEF"
            for character in cor[1:]
        )
    ):
        return JsonResponse({
            "error": "cor inválida"
        }, status=400)

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
            "id": servico.id,
            "nome": servico.nome,
            "preco": str(servico.preco),
            "duracao": servico.duracao,
            "descricao": servico.descricao,
            "ativo": servico.ativo,
            "cor": servico.cor
        }
    }, status=201)


@professional_required
def read_all_services(request):
    if request.method != "GET":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    servicos = Servico.objects.filter(user=user)
    lista_servicos = []

    for servico in servicos:
        lista_servicos.append({
            "id": servico.id,
            "nome": servico.nome,
            "preco": str(servico.preco),
            "duracao": servico.duracao,
            "descricao": servico.descricao,
            "cor": servico.cor,
            "ativo": servico.ativo
        })

    return JsonResponse({
        "servicos": lista_servicos
    }, status=200)


@professional_required
def read_one_service(request, service_id):
    if request.method != "GET":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    servico = Servico.objects.filter(user=user, id=service_id).first()
    if servico is None:
        return JsonResponse({
            "error": "serviço não encontrado"
        }, status=404)

    return JsonResponse({
        "servico": {
            "id": servico.id,
            "nome": servico.nome,
            "preco": str(servico.preco),
            "duracao": servico.duracao,
            "descricao": servico.descricao,
            "cor": servico.cor,
            "ativo": servico.ativo
        }
    })


@professional_required
def update_service(request, service_id):
    if request.method != "PATCH":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    try:
        servico = Servico.objects.get(user=user, id=service_id)
    except Servico.DoesNotExist:
        return JsonResponse({
            "error": "serviço não encontrado"
        }, status=404)

    data, error = parse_json_body(request)
    if error:
        return error

    updated, error = atualizar_servico(request, servico, data)
    if error:
        return JsonResponse({
            "error": str(error)
        }, status=400)

    if not updated:
        return JsonResponse({
            "message": "nenhuma alteração realizada"
        }, status=200)

    return JsonResponse({
        "message": "serviço atualizado",
        "servico": {
            "id": servico.id,
            "nome": servico.nome,
            "preco": str(servico.preco),
            "duracao": servico.duracao,
            "descricao": servico.descricao,
            "cor": servico.cor,
            "ativo": servico.ativo
        }
    })


@professional_required
def delete_service(request, service_id):
    if request.method != "DELETE":
        return JsonResponse({
            "error": "metódo não permitido"
        }, status=405)

    user = request.user

    try:
        servico = Servico.objects.get(user=user, id=service_id)
    except Servico.DoesNotExist:
        return JsonResponse({
            "error": "serviço não encontrado"
        }, status=404)

    servico.delete()

    return JsonResponse({
        "message": "serviço deletado com sucesso"
    }, status=200)
