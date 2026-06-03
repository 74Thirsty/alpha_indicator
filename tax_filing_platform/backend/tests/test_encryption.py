from app.services.encryption_service import EncryptionService


def test_aes_gcm_round_trip() -> None:
    service = EncryptionService()
    aad = b"filing:test"
    encrypted = service.encrypt(b"secret tax document", aad)
    assert encrypted.sha256
    assert service.decrypt(encrypted.ciphertext, nonce_b64=encrypted.nonce_b64, wrapped_key_b64=encrypted.wrapped_key_b64, aad=aad) == b"secret tax document"
