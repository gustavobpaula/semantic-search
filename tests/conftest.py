import hashlib

import pytest
from langchain_core.embeddings import Embeddings

from config import Settings

EMBEDDING_DIMENSION = 8


class FakeEmbeddings(Embeddings):
    """Embeddings determinísticos, sem chamadas externas."""

    def __init__(self):
        self.embedded_texts: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts.extend(texts)
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[i] / 255 for i in range(EMBEDDING_DIMENSION)]


class RecordingStore:
    """Vector store falso que apenas registra os chunks recebidos."""

    def __init__(self):
        self.added_documents = []

    def add_documents(self, documents):
        self.added_documents.extend(documents)
        return [str(index) for index in range(len(documents))]


@pytest.fixture
def fake_embeddings() -> FakeEmbeddings:
    return FakeEmbeddings()


@pytest.fixture
def recording_store() -> RecordingStore:
    return RecordingStore()


@pytest.fixture
def settings(pdf_path) -> Settings:
    return Settings(
        pdf_path=str(pdf_path),
        database_url="postgresql+psycopg://postgres:postgres@localhost:5432/rag",
        collection_name="collection_de_teste",
        embedding_model="text-embedding-3-small",
    )


@pytest.fixture(scope="session")
def pdf_path(pytestconfig):
    return pytestconfig.rootpath / "document.pdf"
