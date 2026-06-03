from __future__ import annotations

import base64
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Tax Filing Platform"
    environment: Literal["local", "test", "staging", "production"] = "local"
    database_url: str = "sqlite+pysqlite:///./tax_filing_local.db"
    jwt_secret: str = Field(default="change-me-only-for-local-dev", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    master_key_b64: str = Field(
        default="MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
        description="Base64 encoded 32 byte AES master key for envelope encryption.",
    )
    max_upload_bytes: int = 10 * 1024 * 1024
    allowed_upload_mime_types: set[str] = {"application/pdf", "image/png", "image/jpeg", "text/plain"}
    storage_root: str = "./var/encrypted_documents"
    eth_rpc_url: str = "http://localhost:8545"
    escrow_contract_address: str | None = None
    operator_private_key: str | None = None
    production_efile_provider_id: str | None = None
    production_efile_api_url: str | None = None
    production_efile_api_key: str | None = None

    @field_validator("master_key_b64")
    @classmethod
    def validate_master_key(cls, value: str) -> str:
        raw = base64.b64decode(value)
        if len(raw) != 32:
            raise ValueError("MASTER_KEY_B64 must decode to exactly 32 bytes")
        return value

    @property
    def master_key(self) -> bytes:
        return base64.b64decode(self.master_key_b64)


@lru_cache
def get_settings() -> Settings:
    return Settings()
