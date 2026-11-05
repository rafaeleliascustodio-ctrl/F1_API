# F1 API

API REST própria de Fórmula 1, feita com FastAPI e PostgreSQL. Armazena pilotos, equipes, circuitos, corridas e resultados no nosso banco e também consulta dados da [OpenF1](https://openf1.org/docs).

Projeto de aprendizado, construído em etapas com arquitetura em camadas.

## Tecnologias

- Python 3.12 ou superior
- FastAPI e Uvicorn
- SQLAlchemy 2.x com psycopg 3
- Pydantic 2
- PostgreSQL (hospedado no Aiven)
- Requests (consumo da OpenF1)
- Pytest e HTTPX (testes)

## Estrutura do projeto

```
F1_API/
├── app/
│   ├── main.py            # aplicação FastAPI e rotas de GET / e GET /health
│   ├── core/              # configurações (config.py)
│   ├── database/          # conexão e Base do SQLAlchemy
│   ├── models/            # tabelas (SQLAlchemy)
│   ├── schemas/           # validação e respostas (Pydantic)
│   ├── repositories/      # acesso ao banco
│   ├── routes/            # endpoints REST
│   └── services/          # integração com a OpenF1
├── tests/                 # testes automatizados
├── create_tables.py       # cria as tabelas no banco
├── .env.example           # modelo do arquivo de configuração
└── requirements.txt
```

## Instalação

Os comandos abaixo são para Windows (PowerShell). Em Linux ou macOS, troque a ativação do ambiente por `source .venv/bin/activate`.

1. Clone o repositório e entre na pasta:

   ```powershell
   git clone https://github.com/rafaeleliascustodio-ctrl/F1_API.git
   cd F1_API
   ```

2. Crie e ative o ambiente virtual:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Instale as dependências:

   ```powershell
   pip install -r requirements.txt
   ```

## Configuração do banco (PostgreSQL no Aiven)

A aplicação lê a conexão da variável `DATABASE_URL`, definida em um arquivo `.env` na raiz do projeto. Esse arquivo **nunca** deve ser commitado: ele já está no `.gitignore`.

1. Copie o modelo:

   ```powershell
   Copy-Item .env.example .env
   ```

2. No painel do Aiven, copie a **Service URI** do seu serviço PostgreSQL e coloque no `.env`:

   ```
   DATABASE_URL=<cole aqui a Service URI do Aiven>
   ```

   O Aiven entrega a URI começando com `postgres://`. Não precisa alterar: o código converte para `postgresql+psycopg://`, formato exigido pelo SQLAlchemy 2.x.

3. Crie as tabelas (uma única vez):

   ```powershell
   python create_tables.py
   ```

## Como rodar

```powershell
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Documentação interativa (Swagger): http://127.0.0.1:8000/docs
- Verificação de saúde (testa a conexão com o banco): http://127.0.0.1:8000/health

## Como testar

```powershell
python -m pytest
```

Os testes **não usam o Aiven nem a internet**:

- O banco é um SQLite em memória, novo a cada teste (usado apenas nos testes; o banco da aplicação é sempre o PostgreSQL).
- As chamadas à OpenF1 são simuladas (mock).
- A rota `/health` fica fora dos testes automatizados, porque depende do banco real.

## Endpoints

Todos os recursos seguem o mesmo padrão REST. Troque `{recurso}` por `drivers`, `teams`, `circuits`, `races` ou `results`.

| Método | Rota | Descrição | Sucesso |
|---|---|---|---|
| GET | `/{recurso}` | Lista (aceita `skip` e `limit`) | 200 |
| GET | `/{recurso}/{id}` | Busca por id | 200 |
| POST | `/{recurso}` | Cria | 201 |
| PATCH | `/{recurso}/{id}` | Atualização parcial (só os campos enviados) | 200 |
| DELETE | `/{recurso}/{id}` | Apaga | 204 |

Rotas adicionais:

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Mensagem de boas-vindas |
| GET | `/health` | Testa a conexão com o banco |
| GET | `/seasons` | Anos distintos, derivados das corridas cadastradas |
| GET | `/openf1/meetings?year=2025` | Grandes Prêmios de um ano (OpenF1) |
| GET | `/openf1/sessions` | Sessões (filtros opcionais: `year`, `session_name`, `meeting_key`) |
| GET | `/openf1/drivers?session_key=9839` | Pilotos de uma sessão |
| GET | `/openf1/session-results?session_key=9839` | Resultado de uma sessão |

A lista completa, com os campos de cada recurso, está no Swagger: http://127.0.0.1:8000/docs

## Exemplos de uso

Criar um piloto:

```powershell
curl.exe -X POST http://127.0.0.1:8000/drivers `
  -H "Content-Type: application/json" `
  -d '{\"first_name\": \"Lewis\", \"last_name\": \"Hamilton\", \"acronym\": \"HAM\", \"number\": 44, \"country_code\": \"GBR\"}'
```

> **Atenção:** a sigla (`acronym`) é única. Se já existir um piloto com a mesma sigla, a API responde **409**. Para repetir o exemplo, use outra sigla ou apague o piloto antes (`DELETE /drivers/{id}`).

Listar com paginação:

```powershell
curl.exe "http://127.0.0.1:8000/drivers?skip=0&limit=10"
```

Atualizar só um campo (troque `1` pelo `id` do piloto, retornado ao criá-lo):

```powershell
curl.exe -X PATCH http://127.0.0.1:8000/drivers/1 `
  -H "Content-Type: application/json" `
  -d '{\"number\": 44}'
```

Consultar a OpenF1 (anos de 2023 em diante):

```powershell
curl.exe "http://127.0.0.1:8000/openf1/meetings?year=2025"
```

Em Linux ou macOS, use `curl` com aspas simples normais no JSON, sem as barras invertidas.

## Regras de validação

| Campo | Regra |
|---|---|
| `acronym` e `country_code` (pilotos) | Exatamente 3 letras maiúsculas (`HAM`, `GBR`) |
| `number` (piloto) | De 1 a 99 |
| `season` (corrida) | De 1950 a 2100 |
| `round` (corrida) | De 1 a 30 |
| `grid` e `position` (resultado) | `grid` de 0 a 30; `position` de 1 a 30, ou `null` se o piloto não terminou |
| `points` (resultado) | Maior ou igual a 0 |

## Códigos de erro

| Código | Quando acontece |
|---|---|
| 404 | Registro inexistente, ou circuito, corrida, piloto ou equipe referenciado que não existe |
| 409 | Duplicidade (sigla, nome, temporada + rodada, corrida + piloto) ou tentativa de apagar um registro com vínculos |
| 422 | Dados inválidos (formato ou faixa de valores) |
| 502 | A OpenF1 falhou ou está indisponível (só nas rotas `/openf1`) |

## Sobre a OpenF1

- Os dados vêm de [openf1.org](https://openf1.org/docs). O histórico é consultado sem autenticação.
- Só há dados de **2023 em diante**. Por isso `/openf1/meetings` rejeita anos anteriores (422).
- Limite do plano gratuito: 3 requisições por segundo e 30 por minuto. Ao exceder, a API responde 502.
- Licença dos dados: **CC BY-NC-SA 4.0**, ou seja, uso **não comercial**.
- As rotas `/openf1` apenas consultam e repassam os dados: nada é gravado no nosso banco.
- Resultados de sessão não trazem pontos nem equipe. A equipe vem de `/openf1/drivers`.
- O campo `country_code` da OpenF1 será removido no fim de 2026, e a API já tolera sua ausência (`null`).