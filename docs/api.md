# Referência da API

## Convenções

- Prefixo comum: `/api`.
- Corpo JSON: endpoints de escrita exigem `Content-Type: application/json`.
- Erros normalmente usam `{ "error": "mensagem" }`.
- JWT profissional usa `Authorization: Bearer <access_token>`.
- Booking e disponibilidade usam o token do cliente.
- Toda resposta passa pelo middleware e recebe `X-Request-ID`.

## Usuários e perfil

| Método e caminho | Auth | Finalidade | Sucesso |
|---|---|---|---:|
| `POST /usr/register` | pública | Cria usuário, perfil e tokens | `200` |
| `POST /usr/login` | pública | Autentica usuário profissional | `200` |
| `GET /usr/me` | JWT | Retorna id, username e email | `200` |
| `GET /usr/me/profile` | JWT | Retorna perfil, expediente e dias | `200` |
| `PATCH /usr/update` | JWT/profissional | Atualiza perfil e expediente parcialmente | `200` |
| `POST /usr/refresh` | pública | Troca refresh token por novo par | `200` |

O `PATCH /usr/update` aceita campos de perfil (`public_slug`, `nome_negocio`,
`telefone`, `endereco`, `instagram`, `descricao`) e de expediente
(`dias_funcionando`, `horario_inicio`, `horario_fim`, `inicio_almoco`,
`fim_almoco`). Campos omitidos permanecem inalterados.

## Serviços

| Método e caminho | Auth | Finalidade | Sucesso |
|---|---|---|---:|
| `POST /serv/create` | profissional | Cria serviço | `201` |
| `GET /serv/read` | profissional | Lista serviços do profissional | `200` |
| `GET /serv/read/<service_id>` | profissional | Consulta um serviço próprio | `200` |
| `PATCH /serv/update/<service_id>` | profissional | Atualiza campos do serviço | `200` |
| `DELETE /serv/delete/<service_id>` | profissional | Remove serviço sem dependência protegida | `200` |

Body de criação/atualização:

```json
{
  "nome": "Corte",
  "preco": "35.00",
  "duracao": 30,
  "descricao": "Descrição opcional",
  "cor": "#000000",
  "ativo": true
}
```

`descricao` é opcional. `cor` usa `#000000` como default quando omitida.
Atualizações são parciais.

## Clientes

| Método e caminho | Auth | Finalidade | Sucesso |
|---|---|---|---:|
| `POST /cli/teste/<slug_barber>` | pública | Identifica/cria cliente e cria vínculo | `201` |
| `GET /cli/read` | cliente | Retorna o próprio cliente | `200` |
| `GET /cli/read/clients` | profissional | Lista clientes vinculados ao profissional | `200` |

Body de identificação:

```json
{
  "nome": "Nome do cliente",
  "telefone": "85999999999"
}
```

O telefone é normalizado e usado como username técnico do usuário cliente.

## Agenda profissional

| Método e caminho | Auth | Finalidade | Sucesso |
|---|---|---|---:|
| `GET /agendar/read` | profissional | Lista agenda do dia ou da data informada | `200` |
| `POST /agendar/create` | profissional | Cria agendamento pelo painel | `201` |
| `PUT /agendar/update/<id_agend>` | profissional | Atualiza cliente, serviços, horário e status | `200` |
| `DELETE /agendar/delete/<id_agend>` | profissional | Cancela agendamento | `200` |
| `PATCH /agendar/status/<id_agend>` | profissional | Atualiza somente o status | `200` |
| `GET /agendar/dashboard` | profissional | Retorna resumo do dia | `200` |
| `GET /agendar/historico` | profissional | Lista agendamentos não pendentes | `200` |

Criação de agendamento:

```json
{
  "cliente_id": 12,
  "servicos": [2, 5],
  "horario_inicio": "2030-01-07T14:00:00-03:00"
}
```

## Booking público

| Método e caminho | Auth | Finalidade | Sucesso |
|---|---|---|---:|
| `GET /public/<slug_barber>/barbearia` | pública | Retorna perfil e serviços ativos | `200` |
| `GET /public/<slug_barber>/horarios` | cliente | Lista horários disponíveis | `200` |
| `POST /public/<slug_barber>/agendar` | cliente | Cria booking público | `201` |

Disponibilidade recebe `data` e uma lista de `servicos` na query string.
Booking recebe:

```json
{
  "servicos": [2],
  "horario_inicio": "2030-01-07T14:00:00-03:00"
}
```

Um horário ocupado retorna `409`, não `400`.

## Códigos relevantes

- `400`: payload, data, horário, serviço ou combinação inválida;
- `401`: token ausente, inválido ou expirado;
- `403`: tipo de usuário sem permissão ou relação de cliente inativa;
- `404`: perfil, serviço, cliente ou agendamento inexistente;
- `409`: conflito de recurso, como horário já ocupado;
- `500`: falha inesperada não representada por uma validação conhecida.
