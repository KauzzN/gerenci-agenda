# Configuração e deploy

## Backend

O backend é uma aplicação Django WSGI. O script [build.sh](../build.sh):

1. instala `requirements.txt`;
2. executa `python manage.py migrate`;
3. executa `python manage.py collectstatic --noinput`.

`gunicorn` está declarado nas dependências, mas o repositório não contém
`render.yaml`, `Procfile` ou um start command versionado. O comando efetivo do
provedor precisa ser confirmado na configuração operacional.

## Frontend

O frontend é construído com Vite:

```bash
npm run build
```

O resultado é publicado pelo ambiente do frontend. O backend não serve esse
bundle neste repositório.

## Variáveis de ambiente do backend

| Variável | Uso |
|---|---|
| `ENVIRONMENT` | `development`, `beta` ou `production` |
| `DEBUG` | habilita debug; deve ser `False` em beta/produção |
| `SECRET_KEY` | chave obrigatória em beta/produção |
| `DATABASE_URL` | banco; obrigatório em beta/produção |
| `ALLOWED_HOSTS` | hosts aceitos; obrigatório em beta/produção |
| `CORS_ALLOWED_ORIGINS` | origens permitidas; obrigatório em beta/produção |
| `CORS_ALLOW_ALL_ORIGINS` | deve permanecer falso em beta/produção |
| `CSRF_TRUSTED_ORIGINS` | origens confiáveis para CSRF |
| `SECURE_SSL_REDIRECT` | redirecionamento HTTPS |
| `SECURE_PROXY_SSL_HEADER_ENABLED` | confiança explícita no proxy HTTPS |
| `SECURE_HSTS_SECONDS` | duração HSTS |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | HSTS para subdomínios |
| `SECURE_HSTS_PRELOAD` | opção HSTS preload |
| `SESSION_COOKIE_SECURE` | cookie de sessão somente HTTPS |
| `CSRF_COOKIE_SECURE` | cookie CSRF somente HTTPS |

Em desenvolvimento, a ausência de `DATABASE_URL` usa SQLite local. Em beta e
produção, a ausência de `DATABASE_URL` causa falha de configuração; SQLite não é
fallback nesses ambientes.

## Variável do frontend

| Variável | Uso |
|---|---|
| `VITE_API_URL` | URL base da API Django |

O build de produção do frontend exige uma URL de API configurada e não deve
apontar para `127.0.0.1`.

## CORS, HTTPS e proxy

As origens CORS são explícitas e `CORS_ALLOW_CREDENTIALS` é falso porque a API
usa o header `Authorization`, não cookies de autenticação.

As configurações seguras possuem defaults para beta/produção, mas HTTPS,
proxy, domínio, certificado e comandos do provedor ainda dependem do ambiente
hospedado.
