# API de Gerenciamento de Contatos (Contact Manager)

API REST para gerenciamento de usuários, autenticação, recuperação de senha e contatos, desenvolvida com FastAPI.

## Visão Geral

- **Arquitetura:** Aplicação assíncrona seguindo o padrão Controller -> Service -> Repository.
- **Banco de Dados:** SQLite com suporte assíncrono via SQLAlchemy 2.0 e `aiosqlite`.
- **Segurança:** Autenticação JWT (Access/Refresh Tokens), hash de senhas com Bcrypt e tokens de recuperação com SHA-256.
- **Recursos:** Verificação de propriedade de recursos (ownership), rate limiting global e headers de segurança.
- **Documentação:** Swagger UI disponível em `/swagger`.

## Tecnologias Utilizadas

- **Framework:** FastAPI & Pydantic v2.
- **Persistência:** SQLAlchemy 2.0 & SQLite.
- **Autenticação:** `python-jose` (JWT) e `bcrypt`.
- **E-mail:** `fastapi-mail` para fluxo de recuperação de senha.
- **Qualidade:** `pytest` (com plugins async e mock), `ruff` (lint/format).
- **Gerenciamento:** Poetry e Taskipy.

## Configuração do Ambiente

### Pré-requisitos

- Python 3.14+
- Poetry

### Instalação

```bash
poetry install
cp .env.example .env
```

### Variáveis de Ambiente Obrigatórias

Configurações necessárias no arquivo `.env`:

- `SECRET_KEY`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`.

_Nota: O banco de dados é criado automaticamente na inicialização. O CORS está configurado para `http://localhost:8080` por padrão._

## Comandos Úteis

| Comando                  | Descrição                               |
| :----------------------- | :-------------------------------------- |
| `poetry run task run`    | Inicia o servidor de desenvolvimento    |
| `poetry run task test`   | Executa a suíte de testes com cobertura |
| `poetry run task lint`   | Executa a verificação do Ruff           |
| `poetry run task format` | Formata o código automaticamente        |

## Endpoints Principais

Acesse `/swagger` para detalhes de payloads e respostas.

### Autenticação e Usuários

- **Registro:** `POST /users/register`
- **Login:** `POST /auth/login` (Retorna Access e Refresh tokens)
- **Token:** `GET /auth/refresh` (Gera novo Access token)
- **Perfil:** `GET /auth/me`
- **Recuperação:** `/auth/forgot-password` e `/auth/reset-password`

### Gerenciamento de Contatos

_Todos os endpoints abaixo exigem token de acesso e validam se o usuário é o dono do recurso._

- **Listagem:** `GET /users/{user_id}/contacts/` (Com paginação)
- **Criação:** `POST /users/{user_id}/contacts/`
- **Edição:** `PUT /users/{user_id}/contacts/{id}`
- **Exclusão:** `DELETE /users/{user_id}/contacts/{id}`

## Segurança

- Rate limiting configurado para `200/dia` e `50/hora`.
- Implementação de headers CSP, HSTS, X-Content-Type e X-Frame-Options.
- As tabelas do SQLite utilizam chaves estrangeiras (ativadas via pragmas de conexão).

## Licença

MIT
