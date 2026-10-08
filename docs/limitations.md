# Known limitations

Esta lista registra somente limitações confirmadas durante as auditorias.

## Deploy operacional

O repositório não versiona `render.yaml`, `Procfile` ou start command do
provedor. A configuração efetiva do Render, domínio, proxy HTTPS e certificados
precisa ser confirmada no ambiente operacional.

## Cenários E2E não reproduzidos manualmente

Durante UX-14, expiração forçada de token e uma corrida manual de dois bookings
no mesmo horário não foram reproduzidas diretamente. Há cobertura automatizada
para refresh, conflito e regras de booking; B2.2 também validou requisições HTTP
concorrentes para isolamento de request ID.

## Logging de acesso após exceção

O evento principal de `django.request` preserva o request ID. A linha de acesso
emitida posteriormente por `django.server` pode aparecer com `request_id=-`
devido ao momento em que o contexto é restaurado.

## Instrumentação de cancelamento

Os fluxos de cancelamento e atualização de status estão em
[agendamento/views.py](../agendamento/views.py), arquivo protegido durante as
etapas anteriores. Eles funcionam pelo contrato atual, mas não possuem eventos
de negócio `booking.cancelled` ou `booking.status_updated` na taxonomia B2.1.

## Frontend fora deste repositório

O frontend é um repositório separado. O README existente nele ainda é baseado
no template do Vite; esta documentação descreve a integração real sem alterar
o worktree frontend protegido.
