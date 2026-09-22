# Busca semântica com LangChain e pgVector

Ambiente local para ingestão de um PDF em PostgreSQL com pgVector e consulta
semântica via OpenAI. A infraestrutura e a ingestão já estão disponíveis; a
busca semântica e o chat serão adicionados nas próximas features.

Este repositório é um fork de
[devfullcycle/mba-ia-desafio-ingestao-busca](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca),
o repositório de exemplo do desafio.

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

Crie sua configuração local:

```bash
cp .env.example .env
```

O `.env.example` vem do repositório de exemplo do desafio e entrega a maioria
dos campos em branco. Edite `.env` e preencha os quatro valores abaixo:

| Variável | Valor |
|---|---|
| `OPENAI_API_KEY` | uma chave criada no painel da OpenAI |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/rag` |
| `PG_VECTOR_COLLECTION_NAME` | `document_embeddings` (ou outro nome de sua escolha) |
| `PDF_PATH` | `document.pdf` |

O prefixo `postgresql+psycopg://` em `DATABASE_URL` é exigido pelo
`langchain-postgres` e não deve ser removido.

`OPENAI_EMBEDDING_MODEL` e `OPENAI_LLM_MODEL` já vêm com valores utilizáveis e
podem ser trocados, mas as duas são obrigatórias: deixá-las em branco
interrompe a execução. A ingestão e a busca devem usar o mesmo modelo de
embeddings. As variáveis `GOOGLE_*` são herdadas do repositório de exemplo e
não são usadas por este projeto — deixe-as como estão.

Não versione o `.env` e não compartilhe a chave.

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
compõem a `DATABASE_URL` indicada na seção anterior.

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

## Ingestão

Com o banco no ar e o `.env` preenchido, ingira o PDF indicado por `PDF_PATH`:

```bash
python src/ingest.py
```

O script carrega o PDF, divide o conteúdo em chunks de 1000 caracteres com 150
de sobreposição, gera um embedding por chunk com `OPENAI_EMBEDDING_MODEL` e
grava tudo na collection `PG_VECTOR_COLLECTION_NAME`. Ao final ele imprime um
resumo:

```text
Ingestão concluída: 34 documentos, 67 chunks na collection 'document_embeddings'.
```

Falhas de configuração, PDF ausente ou ilegível e erros de banco ou da OpenAI
interrompem a execução com mensagem explicativa e código de saída 1.

Cada execução **acrescenta** chunks à collection: rodar a ingestão duas vezes
duplica o conteúdo. Para reingerir do zero, apague a collection (ou o volume,
com `docker compose down -v`) antes.

Ao trocar `OPENAI_EMBEDDING_MODEL` por um modelo de dimensão diferente, a
ingestão se recusa a gravar e pede a remoção da collection ou do volume — sem
isso a collection ficaria com vetores de tamanhos distintos e a busca deixaria
de funcionar.

## Testes

```bash
pytest
```

A suíte padrão é offline: usa dublês no lugar da OpenAI e do banco. O teste de
integração com pgVector é opt-in e exige o banco no ar:

```bash
TEST_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/rag' pytest -m integration
```

Ele cria uma collection temporária com embeddings falsos e a remove ao final,
sem tocar na collection da aplicação.

## Próximas etapas

O chat do terminal (`python src/chat.py`) será implementado nas próximas
features, completando o fluxo:

```bash
docker compose up -d
python src/ingest.py
python src/chat.py
```
