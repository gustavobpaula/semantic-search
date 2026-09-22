# Feature Specification: PDF Ingestion

## Goal

Ler `document.pdf`, dividi-lo conforme os parâmetros obrigatórios, gerar embeddings OpenAI para seus chunks e armazená-los no PostgreSQL com pgVector.

## Functional Requirements

- **FR-1:** `src/ingest.py` deve carregar o conteúdo de `document.pdf`.
- **FR-2:** O conteúdo deve ser dividido com `chunk_size=1000` caracteres e `chunk_overlap=150`.
- **FR-3:** Cada chunk deve ser convertido em embedding por um modelo OpenAI configurado externamente.
- **FR-4:** Os chunks e seus vetores devem ser persistidos no PostgreSQL com pgVector.
- **FR-5:** A ingestão deve usar a configuração de banco e modelos fornecida pela infraestrutura descrita em `docs/specs/01-infrastructure.md`.

## Acceptance Criteria

- **AC-1 [FR-1]:** Com configurações válidas e `document.pdf` presente, `python src/ingest.py` carrega o documento.
- **AC-2 [FR-2]:** O divisor de texto usado pela ingestão está configurado com tamanho 1000 e overlap 150.
- **AC-3 [FR-3]:** A ingestão gera um embedding para cada chunk produzido.
- **AC-4 [FR-4]:** Após a execução, os chunks e embeddings podem ser recuperados da collection no PostgreSQL.
- **AC-5 [FR-5]:** A ingestão utiliza a conexão e os identificadores de modelo fornecidos por configuração externa.

## Constraints

- Aplicam-se as restrições globais de `docs/SPEC.md`.
- A dimensão da collection deve ser compatível com o modelo de embeddings configurado.
- Ao trocar para um modelo com dimensão diferente, a collection existente ou o volume deve ser removido e a ingestão refeita.

## Assumptions

- `document.pdf` é o arquivo fornecido pelo repositório de exemplo do desafio.
- O PDF contém texto que pode ser extraído pelo carregador escolhido.
- A collection é criada na primeira ingestão com a dimensão do modelo configurado.

## Edge Cases

- `document.pdf` ausente ou ilegível.
- Collection existente com dimensão incompatível com o modelo de embeddings.

## Out of Scope

- Nenhum item adicional foi explicitamente excluído.

## Open Questions

- Nenhuma questão permanece aberta.
