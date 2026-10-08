# Autenticação e autorização

## Profissional

`POST /api/usr/login` e `POST /api/usr/register` retornam:

```json
{
  "tokens": {
    "access_token": "...",
    "refresh_token": "..."
  }
}
```

O access token é JWT HS256 com expiração de 15 minutos. O refresh token é um
valor aleatório armazenado no backend somente como hash e expira em 7 dias.
Ao gerar um novo par, refresh tokens ativos anteriores do mesmo usuário são
revogados.

O frontend armazena os tokens profissionais em `localStorage` usando as chaves
`access_token` e `refresh_token`.

## Cliente

O cliente é identificado por `POST /api/cli/teste/<slug>` usando nome e telefone.
A resposta também entrega tokens JWT e o frontend os armazena nas chaves
`client_access_token` e `client_refresh_token`.

O cliente possui contexto separado (`ClientAuthContext`) e não compartilha o
estado de autenticação profissional.

## Refresh e retry

Os dois clientes Axios possuem interceptors independentes:

```text
request com access token
        ↓ 401
consulta refresh token
        ↓
POST /api/usr/refresh
        ↓
salva novo par
        ↓
refaz uma única vez a requisição original
```

Uma Promise compartilhada evita refresh concorrente duplicado. O `_retry` impede
loop infinito.

Quando não há refresh token ou o refresh falha:

- tokens correspondentes são removidos do `localStorage`;
- o frontend dispara `auth:expired` ou `client-auth:expired`;
- o contexto correspondente invalida a sessão.

## Autorização

O backend usa decorators:

- `jwt_required`: exige usuário autenticado;
- `professional_required`: exige usuário com `Profile`;
- `client_required`: exige usuário com `Cliente`.

Falhas de autenticação retornam `401`. Um usuário autenticado sem o perfil
necessário retorna `403`.

## Logout

Não existe endpoint de logout no backend. O logout atual é local:

- profissional: `clearTokens()` e limpeza do `AuthContext`;
- cliente: `clearClientTokens()` e limpeza do `ClientAuthContext`.

O refresh token continua sujeito à expiração/revogação do backend quando
apresentado novamente.

## Rotas do frontend

`PrivateRoute` protege `/dashboard`, `/configuracoes`, `/servicos`,
`/clientes` e `/historico`. `/` e `/register` são públicos. `/book/:slug` é
público para o shell profissional e inicia autenticação separada do cliente.
