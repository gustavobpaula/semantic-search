"""AC-4: chunks e vetores podem ser recuperados da collection no PostgreSQL.

Opt-in: exige um banco com pgVector indicado por TEST_DATABASE_URL, por exemplo
`postgresql+psycopg://postgres:postgres@localhost:5432/rag`.
"""

import os
import uuid

import pytest
from langchain_postgres import PGVector

import ingest
from config import Settings

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not TEST_DATABASE_URL, reason="defina TEST_DATABASE_URL para rodar a integração"
    ),
]


@pytest.fixture
def collection_temporaria(pdf_path, fake_embeddings):
    settings = Settings(
        pdf_path=str(pdf_path),
        database_url=TEST_DATABASE_URL,
        collection_name=f"teste_ingestao_{uuid.uuid4().hex}",
        embedding_model="fake",
    )
    store = PGVector(
        embeddings=fake_embeddings,
        collection_name=settings.collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )
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
