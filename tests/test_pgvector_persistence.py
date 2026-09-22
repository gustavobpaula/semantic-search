"""Integração com pgVector: persistência (spec 02 AC-4) e recuperação (spec 03).

Opt-in: exige um banco com pgVector indicado por TEST_DATABASE_URL, por exemplo
`postgresql+psycopg://postgres:postgres@localhost:5432/rag`.
"""

import os
import uuid

import pytest
from langchain_core.documents import Document
from langchain_postgres import PGVector

import ingest
from conftest import FakeEmbeddings, RecordingLLM
from config import Settings
from search import search_prompt

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL, reason="defina TEST_DATABASE_URL para rodar a integração"
    ),
]


def _conectar(settings, embeddings):
    return PGVector(
        embeddings=embeddings,
        collection_name=settings.collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )


@pytest.fixture
def collection_temporaria(pdf_do_desafio, fake_embeddings):
    settings = Settings(
        pdf_path=str(pdf_do_desafio),
        database_url=TEST_DATABASE_URL,
        collection_name=f"teste_ingestao_{uuid.uuid4().hex}",
        embedding_model="fake",
        llm_model="fake",
    )
    store = _conectar(settings, fake_embeddings)
    yield settings, store
    store.delete_collection()


def test_chunks_e_vetores_ficam_recuperaveis_na_collection(collection_temporaria):
    settings, store = collection_temporaria

    resumo = ingest.ingest(settings=settings, store=store)

    recuperados = store.similarity_search_with_score("faturamento", k=10)
    assert resumo["chunks"] > 0
    assert len(recuperados) == 10
    for documento, score in recuperados:
        assert documento.page_content.strip()
        assert isinstance(score, float)


def test_modelo_de_outra_dimensao_e_recusado_sem_gravar(collection_temporaria):
    """A collection já povoada com 8 dimensões recusa uma ingestão de 16."""
    settings, store = collection_temporaria
    store.add_documents([Document(page_content="conteúdo já ingerido")])

    outra_dimensao = FakeEmbeddings(dimension=16)
    store_incompativel = _conectar(settings, outra_dimensao)

    with pytest.raises(ingest.IngestionError) as erro:
        ingest.ingest(
            settings=settings, store=store_incompativel, embeddings=outra_dimensao
        )

    assert "Remova a collection ou o volume" in str(erro.value)
    # Nada foi acrescentado: a collection segue com o único documento original.
    assert len(store.similarity_search_with_score("conteúdo", k=10)) == 1


def test_a_pergunta_e_vetorizada_e_recupera_chunks_da_collection(
    collection_temporaria, fake_embeddings
):
    """Spec 03 AC-1 e AC-2: a pergunta vira embedding e consulta a collection ingerida."""
    settings, store = collection_temporaria
    ingest.ingest(settings=settings, store=store)
    fake_embeddings.embedded_queries.clear()

    llm = RecordingLLM()
    cadeia = search_prompt(settings=settings, store=store, llm=llm)
    resposta = cadeia.invoke("qual o faturamento?")

    assert fake_embeddings.embedded_queries == ["qual o faturamento?"]
    assert resposta == "resposta da LLM"

    recuperados = store.similarity_search_with_score("qual o faturamento?", k=10)
    contexto = llm.prompts[0].split("CONTEXTO:")[1].split("REGRAS:")[0]
    assert len(recuperados) == 10
    for documento, _score in recuperados:
        assert documento.page_content in contexto
