"""AC-1, AC-3 e AC-5: carregamento, um embedding por chunk e configuração externa."""

import pytest

import ingest
import vector_store
from config import Settings


def test_ingestao_carrega_o_pdf_configurado(settings, recording_store):
    resumo = ingest.ingest(settings=settings, store=recording_store)

    assert resumo["documentos"] == 34
    assert resumo["chunks"] == len(recording_store.added_documents)
    assert resumo["collection"] == settings.collection_name


class StoreQueVetoriza:
    """Dublê que vetoriza os chunks recebidos, como faz o PGVector."""

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.vetores = []

    def add_documents(self, documents):
        self.vetores.extend(
            self.embeddings.embed_documents([documento.page_content for documento in documents])
        )


def test_cada_chunk_produzido_vira_um_embedding(settings, fake_embeddings):
    chunks = ingest.split_documents(ingest.load_documents(settings.pdf_path))
    store = StoreQueVetoriza(fake_embeddings)

    ingest.ingest(settings=settings, store=store)

    assert len(store.vetores) == len(chunks)
    assert fake_embeddings.embedded_texts == [chunk.page_content for chunk in chunks]


def test_store_recebe_os_chunks_na_ordem_produzida(settings, recording_store):
    chunks = ingest.split_documents(ingest.load_documents(settings.pdf_path))

    ingest.ingest(settings=settings, store=recording_store)

    assert [documento.page_content for documento in recording_store.added_documents] == [
        chunk.page_content for chunk in chunks
    ]


def test_clientes_sao_construidos_a_partir_da_configuracao(monkeypatch):
    settings = Settings(
        pdf_path="document.pdf",
        database_url="postgresql+psycopg://usuario:senha@localhost:5432/rag",
        collection_name="minha_collection",
        embedding_model="modelo-de-embeddings",
    )
    argumentos = {}

    monkeypatch.setattr(
        vector_store,
        "OpenAIEmbeddings",
        lambda **kwargs: argumentos.setdefault("embeddings", kwargs),
    )
    monkeypatch.setattr(
        vector_store,
        "PGVector",
        lambda **kwargs: argumentos.setdefault("store", kwargs),
    )

    vector_store.build_vector_store(settings, vector_store.build_embeddings(settings))

    assert argumentos["embeddings"]["model"] == "modelo-de-embeddings"
    assert argumentos["store"]["collection_name"] == "minha_collection"
    assert argumentos["store"]["connection"] == settings.database_url


def test_erro_de_dimensao_orienta_a_recriar_a_collection(settings):
    class StoreIncompativel:
        def add_documents(self, documents):
            raise ValueError("expected 1536 dimensions, not 768")

    with pytest.raises(ingest.IngestionError) as erro:
        ingest.ingest(settings=settings, store=StoreIncompativel())

    assert "Remova a collection ou o volume" in str(erro.value)
