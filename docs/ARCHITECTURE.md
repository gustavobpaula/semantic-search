# Architecture

## Context and Drivers

A aplicação é um pipeline local em Python que ingere um único `document.pdf`, persiste chunks e embeddings no PostgreSQL com pgVector e responde perguntas em uma CLI usando apenas o contexto recuperado (`docs/SPEC.md FR-1`; `docs/specs/02-pdf-ingestion.md FR-1–FR-4`; `docs/specs/03-semantic-retrieval.md FR-1–FR-6`; `docs/specs/04-cli-chat.md FR-1, FR-2, FR-5, FR-6`).

As interfaces públicas permanecem `docker compose up -d`, `python src/ingest.py` e `python src/chat.py` (`docs/SPEC.md AC-1`). A arquitetura deve privilegiar simplicidade, configuração externa e testes sem chamadas reais obrigatórias à OpenAI.

## Technology Baseline

| Concern | Decision | Role | Rationale or constraint |
|---|---|---|---|
| Language/runtime | Python 3, execução síncrona | Scripts e fluxo da aplicação | Exigido por `docs/SPEC.md` e adequado à CLI local |
| Application framework | LangChain | Carregamento, divisão, modelos e vector store | Exigido por `docs/SPEC.md`, seção Constraints |
| Models | OpenAI via LangChain | Embeddings e geração da resposta | `docs/SPEC.md` Constraints; identificadores externos |
| Persistence | PostgreSQL com pgVector | Chunks, metadados e vetores | `docs/specs/02-pdf-ingestion.md FR-4` |
| Local infrastructure | Docker Compose do repositório de exemplo | Banco reproduzível | `docs/specs/01-infrastructure.md FR-1`; o arquivo é fixado a montante e não é redesenhado aqui |
| Packaging | `requirements.txt` e virtualenv | Dependências reproduzíveis | `docs/specs/01-infrastructure.md FR-2, AC-2` |
| Configuration | Variáveis de ambiente documentadas em `.env.example` | Banco, chave e modelos | `docs/specs/01-infrastructure.md FR-3` |
| Testing | pytest, com dublês nas fronteiras externas | Testes unitários e de integração | Evitar custo e não determinismo da OpenAI |

## Architectural Style and Boundaries

Adotar um pipeline modular compacto:

```text
document.pdf → ingestão → embeddings → pgVector
                                          ↑
CLI → pergunta → recuperação semântica ───┘
                 recuperação → contexto + prompt → LLM → resposta → CLI
```

Ingestão, recuperação e chat são capacidades distintas. A recuperação é dona da composição do contexto, do prompt obrigatório e da chamada à LLM (`docs/specs/03-semantic-retrieval.md FR-4–FR-6`); ao chat cabe a interação no terminal. Configuração e construção de clientes podem ser compartilhadas, sem criar camadas de domínio, repositories genéricos ou interfaces de provedor sem uma segunda implementação concreta.

## Directory Organization

| Pattern | Responsibility | Allowed dependencies | Forbidden contents or dependencies |
|---|---|---|---|
| Root | Configuração, dependências, documento e infraestrutura | Docker Compose e arquivos de configuração | Credenciais reais e lógica da aplicação |
| `src/` | Entrypoints obrigatórios e módulos coesos do pipeline | Python, LangChain e integrações aprovadas | Estado global mutável, segredos e dependência de testes |
| `tests/` | Testes unitários e de integração | Código de `src/`, dublês e banco de teste | Lógica reutilizada pela aplicação |
| `docs/` | Especificação e decisões arquiteturais | Referências entre documentos | Código executável e configuração secreta |

`src/ingest.py`, `src/search.py` e `src/chat.py` são contratos de execução definidos por `docs/SPEC.md`; a decomposição interna adicional permanece responsabilidade da implementação. A fronteira pública da recuperação é `search_prompt()` em `src/search.py` (`docs/specs/03-semantic-retrieval.md FR-5–FR-6`).

## Dependency Rules

- O chat pode depender da fronteira pública de recuperação; a recuperação não pode depender do chat.
- O chat não monta o prompt nem chama a LLM por caminho próprio; ambos pertencem à recuperação.
- A ingestão e a recuperação devem reutilizar a mesma configuração de embeddings, collection e banco.
- Entrypoints coordenam o fluxo, mas regras reutilizáveis não devem depender de entrada ou saída do terminal.
- Código de integração não deve importar entrypoints.
- Tipos ou abstrações genéricas só devem ser introduzidos quando houver comportamento compartilhado ou uma fronteira de teste concreta.

## State and Data Ownership

PostgreSQL/pgVector é o único proprietário do estado persistente. A collection contém os chunks e embeddings do documento. Pergunta, resultados recuperados, contexto e resposta são transitórios e pertencem ao processo da CLI.

Configuração é carregada no início de cada processo e tratada como imutável. Ingestão e busca devem usar o mesmo modelo de embeddings e a mesma collection; incompatibilidade dimensional exige recriação da collection ou do volume (`docs/specs/02-pdf-ingestion.md Constraints`).

## External Integrations

- OpenAI: embeddings e LLM acessados exclusivamente pela integração LangChain, com chave e modelos externos.
- PostgreSQL/pgVector: persistência e similaridade vetorial.
- Sistema de arquivos: leitura de `document.pdf`.

Cada integração deve possuir um ponto pequeno e substituível de construção ou chamada para permitir testes. Falhas de configuração, arquivo, banco ou provedor devem interromper o fluxo com mensagem clara, sem expor credenciais.

## Domain Rules

- Divisão: `chunk_size=1000` e `chunk_overlap=150` (`docs/specs/02-pdf-ingestion.md FR-2`).
- Recuperação: mesma collection e `similarity_search_with_score(query, k=10)` (`docs/specs/03-semantic-retrieval.md FR-2–FR-3`).
- O contexto contém os chunks na ordem retornada (`docs/specs/03-semantic-retrieval.md FR-4`).
- O prompt obrigatório não pode ser alterado nem ter suas regras de fundamentação enfraquecidas (`docs/specs/03-semantic-retrieval.md FR-5, AC-5`).
- Ausência de informação ou solicitação de opinião deve produzir exatamente `Não tenho informações necessárias para responder sua pergunta.` (`docs/specs/03-semantic-retrieval.md FR-5`; `docs/specs/04-cli-chat.md FR-6`).

## Naming Conventions

Diretórios, módulos, funções e variáveis usam `snake_case`; classes usam `PascalCase`; constantes usam `SCREAMING_SNAKE_CASE`; testes usam `test_<comportamento>.py`. Nomes devem expressar a capacidade do pipeline, não detalhes acidentais do provedor.

## Feature Extension Rules

- Toda nova feature deve declarar seu proprietário de estado, respeitar a direção das dependências e possuir testes proporcionais.
- Uma feature pode usar módulos compartilhados quando houver comportamento realmente reutilizado.
- Uma feature não deve acessar pgVector ou OpenAI por caminhos paralelos, duplicar configuração ou alterar os entrypoints públicos sem mudança aprovada na especificação.

## Testing Strategy

Testes unitários cobrem divisão, composição do contexto, prompt e tratamento de ausência usando dublês de embeddings, vector store e LLM. Testes de integração validam persistência e recuperação em PostgreSQL/pgVector real. Um smoke test ponta a ponta com OpenAI é opt-in e exige credenciais; não substitui testes determinísticos.

## Decisions and Trade-offs

- **AD-1 — Pipeline síncrono compacto.** Atende `docs/SPEC.md FR-1` com menor custo estrutural; não oferece paralelismo ou serviço permanente.
- **AD-2 — pgVector como única fonte persistente.** Atende `docs/specs/02-pdf-ingestion.md FR-4` e `docs/specs/03-semantic-retrieval.md FR-2`; acopla o ciclo da collection à dimensão do embedding.
- **AD-3 — Integrações concretas com seams de teste, sem abstrações genéricas.** OpenAI e pgVector são os únicos provedores aprovados; reduz indireção, preservando testabilidade.
- **AD-4 — Configuração externa compartilhada.** Atende `docs/specs/01-infrastructure.md FR-3` e evita divergência entre ingestão e busca.
- **AD-5 — Scripts obrigatórios como contratos públicos.** Preserva `docs/SPEC.md AC-1`; refatorações internas não podem alterar os comandos documentados.

## Deferred Decisions

- **DD-1 — Reingestão e deduplicação.** Definir somente quando a especificação exigir executar ingestões repetidas sem recriar a collection.
- **DD-2 — Suporte a múltiplos documentos.** Reconsiderar quando deixar de valer a premissa de documento único em `docs/SPEC.md`, seção Assumptions.
