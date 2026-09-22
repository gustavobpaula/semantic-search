"""AC-1, AC-3 e AC-5: carregamento, um embedding por chunk e configuração externa."""

import pytest

import ingest
import vector_store
from conftest import PAGINAS_DE_AMOSTRA, FakeEmbeddings
from config import Settings
from search import SearchError


def test_ingestao_carrega_o_pdf_configurado(settings, recording_store):
    resumo = ingest.ingest(settings=settings, store=recording_store)

    assert resumo["documentos"] == PAGINAS_DE_AMOSTRA
    assert resumo["chunks"] == len(recording_store.added_documents)
    assert resumo["collection"] == settings.collection_name


class StoreQueVetoriza:
    """Dublê que vetoriza os chunks recebidos, como faz o PGVector."""

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.vetores = []

    def similarity_search_by_vector(self, embedding, k=4):
        return []

    def add_documents(self, documents):
        self.vetores.extend(
            self.embeddings.embed_documents([documento.page_content for documento in documents])
        )


def test_cada_chunk_produzido_vira_um_embedding(settings, fake_embeddings):
    chunks = ingest.split_documents(ingest.load_documents(settings.pdf_path))
    store = StoreQueVetoriza(fake_embeddings)

    ingest.ingest(settings=settings, store=store, embeddings=fake_embeddings)

    assert len(store.vetores) == len(chunks)
    # A sondagem de dimensão usa embed_query, então só os chunks entram aqui.
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
        llm_model="modelo-de-llm",
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
    monkeypatch.setattr(
        vector_store,
        "ChatOpenAI",
        lambda **kwargs: argumentos.setdefault("llm", kwargs),
    )

    vector_store.build_vector_store(settings, vector_store.build_embeddings(settings))
    vector_store.build_llm(settings)

    assert argumentos["embeddings"]["model"] == "modelo-de-embeddings"
    assert argumentos["store"]["collection_name"] == "minha_collection"
    assert argumentos["store"]["connection"] == settings.database_url
    assert argumentos["llm"]["model"] == "modelo-de-llm"


def test_dimensao_divergente_interrompe_antes_de_gravar(settings, fake_embeddings):
    class StoreDeOutraDimensao:
        def __init__(self):
            self.added_documents = []

        def similarity_search_by_vector(self, embedding, k=4):
            raise ValueError("different vector dimensions 8 and 1536")

        def add_documents(self, documents):
            self.added_documents.extend(documents)

    store = StoreDeOutraDimensao()

    with pytest.raises(ingest.IngestionError) as erro:
        ingest.ingest(settings=settings, store=store, embeddings=fake_embeddings)

    assert "Remova a collection ou o volume" in str(erro.value)
    assert store.added_documents == []


def test_erro_de_dimensao_na_escrita_tambem_orienta_a_recriar(settings):
    class StoreIncompativel:
        def add_documents(self, documents):
            raise ValueError("expected 1536 dimensions, not 768")

    with pytest.raises(ingest.IngestionError) as erro:
        ingest.ingest(settings=settings, store=StoreIncompativel())

    assert "Remova a collection ou o volume" in str(erro.value)


def test_falha_de_conexao_na_ingestao_vira_mensagem_clara(settings, monkeypatch):
    def recusa_conexao(*args, **kwargs):
        raise RuntimeError("connection failed: FATAL: password authentication failed")

    monkeypatch.setattr(vector_store, "PGVector", recusa_conexao)
    monkeypatch.setattr(ingest, "build_embeddings", lambda settings: FakeEmbeddings())

    with pytest.raises(ingest.IngestionError) as erro:
        ingest.ingest(settings=settings)

    mensagem = str(erro.value)
    assert "Não foi possível conectar ao PostgreSQL" in mensagem
    assert "docker compose up -d" in mensagem


@pytest.mark.parametrize("classe_de_erro", [ingest.IngestionError, SearchError])
def test_wrapper_de_conexao_traduz_o_erro_de_cada_capacidade(
    monkeypatch, settings, fake_embeddings, classe_de_erro
):
    """O wrapper compartilhado traduz a falha no tipo de erro de cada capacidade."""

    def explode(**kwargs):
        raise RuntimeError("could not connect to server")

    monkeypatch.setattr(vector_store, "PGVector", explode)

    with pytest.raises(classe_de_erro) as erro:
        vector_store.connect_vector_store(settings, fake_embeddings, classe_de_erro)

    assert "Não foi possível conectar ao PostgreSQL" in str(erro.value)
    assert "could not connect to server" in str(erro.value)
