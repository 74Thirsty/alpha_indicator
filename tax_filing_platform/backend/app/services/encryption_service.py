from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..config import Settings, get_settings


@dataclass(frozen=True)
class EncryptionResult:
    ciphertext: bytes
    nonce_b64: str
    wrapped_key_b64: str
    sha256: str


class EncryptionService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._master = AESGCM(self.settings.master_key)

    def encrypt(self, plaintext: bytes, aad: bytes) -> EncryptionResult:
        data_key = AESGCM.generate_key(bit_length=256)
        file_nonce = os.urandom(12)
        ciphertext = AESGCM(data_key).encrypt(file_nonce, plaintext, aad)
        wrap_nonce = b"\x00" * 12
        wrapped = self._master.encrypt(wrap_nonce, data_key, aad)
        return EncryptionResult(
            ciphertext=ciphertext,
            nonce_b64=base64.b64encode(file_nonce).decode(),
            wrapped_key_b64=base64.b64encode(wrapped).decode(),
            sha256=hashlib.sha256(plaintext).hexdigest(),
        )

    def decrypt(self, ciphertext: bytes, *, nonce_b64: str, wrapped_key_b64: str, aad: bytes) -> bytes:
        data_key = self._master.decrypt(b"\x00" * 12, base64.b64decode(wrapped_key_b64), aad)
        return AESGCM(data_key).decrypt(base64.b64decode(nonce_b64), ciphertext, aad)
