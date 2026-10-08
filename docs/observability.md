# Observabilidade

## Request ID

O middleware `ApiMiddleware` lê `X-Request-ID` em cada requisição.

- valores aceitos seguem `[A-Za-z0-9._~-]{1,64}`;
- valor ausente ou inválido recebe UUID v4;
- o valor fica no `ContextVar` durante a requisição;
- a resposta devolve o mesmo valor em `X-Request-ID`;
- o formatter do console inclui `request_id=...`.

O contexto também carrega método e caminho da requisição. O middleware mede a
duração, embora o evento de duração não seja emitido automaticamente para todo
GET.

## Eventos de negócio

Eventos atualmente emitidos:

### Autenticação e autorização

- `auth.register_success`
- `auth.register_failed`
- `auth.login_success`
- `auth.login_failed`
- `auth.refresh_failed`
- `auth.unauthorized`
- `auth.forbidden`

### Booking

- `booking.created`
- `booking.conflict`

### Cliente

- `client.created`
- `client.professional_linked`

### Serviço

- `service.created`
- `service.updated`
- `service.status_updated`
- `service.deleted`

### Perfil e expediente

- `profile.updated`
- `schedule.updated`

Os eventos incluem somente contexto operacional necessário, como IDs, status,
método e caminho.

## Formatação e níveis

O console usa linhas legíveis com data, nível, request ID e campos do evento.
Falhas de autenticação e validações de autorização usam `WARNING`. Eventos
bem-sucedidos usam `INFO`. Exceções inesperadas usam o logger padrão
`django.request` em `ERROR`.

## Proteção de dados

`log_event` bloqueia campos sensíveis, incluindo:

- `password`;
- `access_token`;
- `refresh_token`;
- `jwt`;
- `authorization`;
- `cookie`;
- `secret_key`;
- `database_url`;
- corpo e parâmetros completos da requisição.

Não registrar payloads completos ou dados pessoais apenas para facilitar
debug.

## Limites conhecidos

O logger de acesso `django.server` pode emitir uma linha posterior com
`request_id=-` após uma exceção, porque o contexto do middleware já foi
restaurado. O traceback principal de `django.request` mantém o request ID.
