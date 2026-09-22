import hashlib

import pytest
from langchain_core.embeddings import Embeddings

from config import Settings

EMBEDDING_DIMENSION = 8


class FakeEmbeddings(Embeddings):
    """Embeddings determinísticos, sem chamadas externas."""

    def __init__(self, dimension: int = EMBEDDING_DIMENSION):
        self.dimension = dimension
        self.embedded_texts: list[str] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.embedded_texts.extend(texts)
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [digest[indice % len(digest)] / 255 for indice in range(self.dimension)]


class RecordingStore:
    """Vector store falso que apenas registra os chunks recebidos."""

    def __init__(self):
        self.added_documents = []

    def similarity_search_by_vector(self, embedding, k=4):
        return []

    def add_documents(self, documents):
        self.added_documents.extend(documents)
        return [str(index) for index in range(len(documents))]


def build_pdf(paginas: list[str]) -> bytes:
    """Monta um PDF mínimo com uma página por texto recebido."""
    ids_paginas = [4 + 2 * indice for indice in range(len(paginas))]
    objetos = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [%s] /Count %d >>"
        % (" ".join(f"{pid} 0 R" for pid in ids_paginas), len(paginas)),
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    for indice, texto in enumerate(paginas):
        pid = ids_paginas[indice]
        linhas = [texto[inicio:inicio + 90] for inicio in range(0, len(texto), 90)]
        conteudo = (
            "BT /F1 10 Tf 40 750 Td 12 TL\n"
            + "".join(f"({linha}) Tj T*\n" for linha in linhas)
            + "ET"
        )
        objetos.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {pid + 1} 0 R >>"
        )
        objetos.append(f"<< /Length {len(conteudo)} >>\nstream\n{conteudo}\nendstream")

    saida = bytearray(b"%PDF-1.4\n")
    offsets = []
    for numero, corpo in enumerate(objetos, start=1):
        offsets.append(len(saida))
        saida += f"{numero} 0 obj\n{corpo}\nendobj\n".encode("latin-1")

    inicio_xref = len(saida)
    saida += f"xref\n0 {len(objetos) + 1}\n".encode("latin-1")
    saida += b"0000000000 65535 f \n"
    for offset in offsets:
        saida += f"{offset:010d} 00000 n \n".encode("latin-1")
    saida += (
        f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
        f"startxref\n{inicio_xref}\n%%EOF\n"
    ).encode("latin-1")
    return bytes(saida)


PAGINAS_DE_AMOSTRA = 3


@pytest.fixture(scope="session")
def pdf_de_amostra(tmp_path_factory):
    """PDF determinístico de 3 páginas, cada uma com texto para vários chunks."""
    paginas = [
        " ".join(f"pagina{numero}palavra{indice}" for indice in range(120))
        for numero in range(PAGINAS_DE_AMOSTRA)
    ]
    caminho = tmp_path_factory.mktemp("pdfs") / "amostra.pdf"
    caminho.write_bytes(build_pdf(paginas))
    return caminho


@pytest.fixture(scope="session")
def pdf_do_desafio(pytestconfig):
    """O `document.pdf` real, usado apenas nos testes de integração."""
    return pytestconfig.rootpath / "document.pdf"


@pytest.fixture
def fake_embeddings() -> FakeEmbeddings:
    return FakeEmbeddings()


@pytest.fixture
def recording_store() -> RecordingStore:
    return RecordingStore()


@pytest.fixture
def settings(pdf_de_amostra) -> Settings:
    return Settings(
        pdf_path=str(pdf_de_amostra),
        database_url="postgresql+psycopg://postgres:postgres@localhost:5432/rag",
        collection_name="collection_de_teste",
        embedding_model="text-embedding-3-small",
    )
