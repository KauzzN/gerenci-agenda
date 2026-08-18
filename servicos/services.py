from servicos.models import Servico
from decimal import Decimal, InvalidOperation

def atualizar_servico(request, servico, data):

    updated = False

    if "nome" in data and data["nome"].strip():

        nome = data["nome"].strip()

        if nome != servico.nome:

            servico.nome = nome
            updated = True

    if "preco" in data and data["preco"].strip():

        preco = data["preco"].strip()

        try:
            preco = Decimal(preco)

        except InvalidOperation:
            return None, "preço deve ser um número válido"

        if preco != servico.preco:

            servico.preco = preco
            updated = True


    if "duracao" in data and data["duracao"].strip():

        duracao = data["duracao"].strip()

        if not duracao.isdigit():
            return None, "duração precisa ser número"

        duracao = int(duracao)

        if duracao != servico.duracao:
             
            servico.duracao = duracao
            updated = True

    if "descricao" in data and data["descricao"].strip():
    
        descricao = data["descricao"].strip()

        if len(descricao) > 200:
            return None, "Descrição muito longa"

        if descricao != servico.descricao:

            servico.descricao = descricao
            updated = True

    if "cor" in data and data["cor"].strip():

        cor = data["cor"].strip()

        if not cor.startswith("#"):
            return None, "cor inválida"

        if cor != servico.cor:

            servico.cor = cor
            updated = True

    if "ativo" in data and data["ativo"]:


        ativo = data["ativo"]

        if ativo != servico.ativo:

            servico.ativo = ativo
            updated = True

    if updated:
        servico.save()

    return updated, None
        

        