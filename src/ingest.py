"""Ingestão de `document.pdf` na collection pgVector."""

import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import ConfigError, Settings, load_settings
from vector_store import build_embeddings, build_vector_store

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

DICA_DE_DIMENSAO = (
    "A collection já contém vetores de outra dimensão, gerados por um modelo de "
    "embeddings diferente. Remova a collection ou o volume do banco e refaça a "
    "ingestão."
)


class IngestionError(Exception):
    """Falha impeditiva durante a ingestão."""


def load_documents(pdf_path: str) -> list[Document]:
    path = Path(pdf_path)
    if not path.is_file():
        raise IngestionError(f"PDF não encontrado em '{pdf_path}'.")

    try:
        return PyPDFLoader(str(path)).load()
    except Exception as error:
        raise IngestionError(f"Não foi possível ler o PDF '{pdf_path}': {error}") from error


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    return [chunk for chunk in chunks if chunk.page_content.strip()]


def _primeira_linha(error: Exception) -> str:
    """Resumo legível do erro; a causa completa segue encadeada na exceção."""
    return str(error).splitlines()[0]


def connect_vector_store(settings: Settings, embeddings) -> object:
    """Conecta na collection, traduzindo falhas de banco em mensagem clara."""
    try:
        return build_vector_store(settings, embeddings)
    except Exception as error:
        raise IngestionError(
            "Não foi possível conectar ao PostgreSQL. Verifique DATABASE_URL no "
            ".env e se o banco está no ar (`docker compose up -d`).\n"
            f"Detalhe: {_primeira_linha(error)}"
        ) from error


def ensure_compatible_dimension(store, embeddings) -> None:
    """Falha antes de gravar quando a collection tem outra dimensão.

    A tabela do pgVector não fixa a dimensão da coluna, então vetores de
    tamanhos diferentes são aceitos na escrita e só quebram na busca. Uma
    consulta de sondagem com um vetor do modelo atual antecipa o conflito.
    """
    sonda = embeddings.embed_query("sondagem de dimensão")
    try:
        store.similarity_search_by_vector(sonda, k=1)
    except Exception as error:
        if "dimension" in str(error).lower():
            raise IngestionError(
                f"{DICA_DE_DIMENSAO}\nDetalhe: {_primeira_linha(error)}"
            ) from error
        raise IngestionError(
            f"Falha ao consultar a collection antes da ingestão: {_primeira_linha(error)}"
        ) from error


def store_chunks(chunks: list[Document], store) -> None:
    try:
        store.add_documents(chunks)
    except Exception as error:
        message = f"Falha ao gerar os embeddings ou gravar os chunks: {error}"
        if "dimension" in str(error).lower():
            message += f"\n{DICA_DE_DIMENSAO}"
        raise IngestionError(message) from error


def ingest(settings: Settings | None = None, store=None, embeddings=None) -> dict:
    settings = settings or load_settings()
    documents = load_documents(settings.pdf_path)
    chunks = split_documents(documents)

    if not chunks:
        raise IngestionError(
            f"Nenhum texto extraível encontrado em '{settings.pdf_path}'."
        )

    if store is None:
        embeddings = embeddings or build_embeddings(settings)
        store = connect_vector_store(settings, embeddings)

    if embeddings is not None:
        ensure_compatible_dimension(store, embeddings)

    store_chunks(chunks, store)

    return {
        "documentos": len(documents),
        "chunks": len(chunks),
        "collection": settings.collection_name,
    }


def main() -> int:
    try:
        summary = ingest()
    except (ConfigError, IngestionError) as error:
        print(error, file=sys.stderr)
        return 1

    print(
        f"Ingestão concluída: {summary['documentos']} documentos, "
        f"{summary['chunks']} chunks na collection '{summary['collection']}'."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
