# Busca semântica com LangChain e pgVector

Ambiente local para ingestão de um PDF em PostgreSQL com pgVector e consulta
semântica via OpenAI. Esta etapa configura a infraestrutura; os scripts de
ingestão e chat serão adicionados nas próximas features.

## Pré-requisitos

- Python 3.11 ou superior
- Docker Desktop (ou Docker Engine) com Docker Compose v2
- Uma chave de API da OpenAI, usada posteriormente para embeddings e chat

Confirme que `python3 --version` indica 3.11 ou superior. No macOS, a fórmula
`python@3.11` do Homebrew também disponibiliza `python3.11`; se `python3`
continuar apontando para uma versão anterior, use `python3.11 -m venv venv` no
comando abaixo ou inclua `/opt/homebrew/opt/python@3.11/libexec/bin` no `PATH`.

## Configuração

Crie e ative um ambiente virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie sua configuração local e preencha somente a chave da OpenAI:

```bash
cp .env.example .env
```

Edite `.env` e defina `OPENAI_API_KEY` com uma chave criada no painel da
OpenAI. Não versione esse arquivo e não compartilhe a chave. Os modelos podem
ser alterados por `OPENAI_EMBEDDING_MODEL` e `OPENAI_LLM_MODEL`; a ingestão e a
busca deverão usar o mesmo modelo de embeddings.

## Banco de dados

Inicie o PostgreSQL e o bootstrap da extensão pgVector:

```bash
docker compose up -d
```

Verifique que os serviços estão saudáveis e que a extensão foi criada:

```bash
docker compose ps
docker compose exec postgres psql -U postgres -d rag -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

O banco fica disponível em `localhost:5432`, com usuário `postgres`, senha
`postgres` e banco `rag`. Esses valores são defaults exclusivamente locais e
correspondem a `DATABASE_URL` em `.env.example`.

Para parar o banco preservando seus dados:

```bash
docker compose down
```

Ao trocar o modelo de embeddings por outro com dimensão diferente, remova a
collection ou recrie o banco antes de ingerir novamente. Para apagar todo o
banco local e seu volume, use o comando destrutivo abaixo:

```bash
docker compose down -v
```

## Próximas etapas

Após as features de ingestão e chat serem implementadas, o fluxo completo será:

```bash
docker compose up -d
python src/ingest.py
python src/chat.py
```
