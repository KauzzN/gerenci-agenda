# Decisões arquiteturais

## `dias_funcionando=[]`

Lista vazia significa agenda não configurada. Não é um curinga para todos os
dias. A disponibilidade bloqueia horários quando não há dias configurados.

## Domingo

Domingo é tratado como qualquer outro dia configurável. Sua presença na lista
habilita o dia; sua ausência o desabilita.

## Booking e conflito

Conflito de horário no booking público é uma condição de negócio e retorna
`409`. O frontend limpa o horário e recarrega a disponibilidade para permitir
recuperação.

## Tokens separados

Profissional e cliente usam tokens e chaves de armazenamento distintas. Isso
evita que a sessão pública do cliente interfira na sessão do painel.

## Refresh com Promise compartilhada

Cada Axios autenticado compartilha uma Promise de refresh para impedir várias
renovações simultâneas. A requisição original é repetida no máximo uma vez.

## Evento de sessão expirada

O interceptor detecta falha de refresh, limpa o armazenamento e dispara um
evento (`auth:expired` ou `client-auth:expired`). Os contexts React refletem a
invalidação para a interface.

## Logging por request

Request ID é mantido em `ContextVar` e retornado no header da resposta. Eventos
de negócio são preferidos a registrar todos os payloads e GETs, reduzindo ruído
e exposição de dados.

## Produção sem SQLite

Beta e produção exigem `DATABASE_URL`. O SQLite é reservado para desenvolvimento
local e testes.

## Booking fora do shell profissional

`/book/:slug` é rota pública do frontend. Ela não usa `PrivateRoute` e possui
contexto/token de cliente separado.

## Logout local

Não há endpoint de logout. O frontend remove access e refresh tokens e atualiza
o contexto local. A revogação server-side ocorre quando o backend recebe
refresh tokens revogados ou expirados.
