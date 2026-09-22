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


def store_chunks(chunks: list[Document], store) -> None:
    try:
        store.add_documents(chunks)
    except Exception as error:
        message = f"Falha ao gerar os embeddings ou gravar os chunks: {error}"
        if "dimension" in str(error).lower():
            message += (
                "\nA collection existente foi criada com outra dimensão de vetor. "
                "Remova a collection ou o volume do banco e refaça a ingestão."
            )
        raise IngestionError(message) from error


def ingest(settings: Settings | None = None, store=None) -> dict:
    settings = settings or load_settings()
    documents = load_documents(settings.pdf_path)
    chunks = split_documents(documents)

    if not chunks:
        raise IngestionError(
            f"Nenhum texto extraível encontrado em '{settings.pdf_path}'."
        )

    store = store or build_vector_store(settings, build_embeddings(settings))
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
