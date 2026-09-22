"""Configuração externa compartilhada pela ingestão e pela busca."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from dotenv import load_dotenv

REQUIRED_VARIABLES = (
    "OPENAI_API_KEY",
    "OPENAI_EMBEDDING_MODEL",
    "OPENAI_LLM_MODEL",
    "DATABASE_URL",
    "PG_VECTOR_COLLECTION_NAME",
    "PDF_PATH",
)


class ConfigError(Exception):
    """Configuração ausente ou inválida."""


@dataclass(frozen=True)
class Settings:
    pdf_path: str
    database_url: str
    collection_name: str
    embedding_model: str
    llm_model: str


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Lê a configuração do ambiente.

    Sem `env`, carrega o `.env` e usa as variáveis do processo. A chave da
    OpenAI é apenas validada: ela é consumida pelo cliente diretamente do
    ambiente e nunca é guardada aqui.
    """
    if env is None:
        load_dotenv()
        env = os.environ

    missing = [name for name in REQUIRED_VARIABLES if not (env.get(name) or "").strip()]
    if missing:
        raise ConfigError(
            "Configuração incompleta. Defina no .env: " + ", ".join(missing)
        )

    return Settings(
        pdf_path=env["PDF_PATH"].strip(),
        database_url=env["DATABASE_URL"].strip(),
        collection_name=env["PG_VECTOR_COLLECTION_NAME"].strip(),
        embedding_model=env["OPENAI_EMBEDDING_MODEL"].strip(),
        llm_model=env["OPENAI_LLM_MODEL"].strip(),
    )
