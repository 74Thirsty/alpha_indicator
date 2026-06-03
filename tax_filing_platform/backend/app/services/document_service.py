from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..integrations.storage_provider import LocalEncryptedStorageProvider, StorageProvider
from ..models.document import Document
from ..models.filing import Filing
from ..security.input_validation import validate_upload_metadata
from .audit_service import AuditService
from .encryption_service import EncryptionService
from .tax_validation_service import TaxValidationService


class DocumentService:
    def __init__(self, db: Session, storage: StorageProvider | None = None):
        self.db = db
        self.settings = get_settings()
        self.storage = storage or LocalEncryptedStorageProvider(self.settings.storage_root)
        self.encryption = EncryptionService(self.settings)
        self.validator = TaxValidationService()
        self.audit = AuditService(db)

    async def upload(self, *, filing: Filing, user_id: str, file: UploadFile) -> Document:
        data = await file.read()
        validate_upload_metadata(file, len(data), self.settings)
        validation = self.validator.validate_tax_document(file.filename or "document", data)
        if not validation.accepted:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=validation.findings)
        aad = f"filing:{filing.id}:user:{user_id}".encode()
        encrypted = self.encryption.encrypt(data, aad)
        key = f"{filing.id}/{uuid4()}.bin"
        self.storage.put(key, encrypted.ciphertext)
        doc = Document(
            filing_id=filing.id,
            user_id=user_id,
            filename=file.filename or "document",
            mime_type=file.content_type or "application/octet-stream",
            sha256=encrypted.sha256,
            storage_key=key,
            wrapped_key_b64=encrypted.wrapped_key_b64,
            nonce_b64=encrypted.nonce_b64,
            size_bytes=len(data),
        )
        self.db.add(doc)
        self.db.flush()
        self.audit.log(actor_user_id=user_id, action="document.uploaded", target_type="document", target_id=doc.id, metadata={"filing_id": filing.id, "sha256": doc.sha256})
        self.db.commit()
        self.db.refresh(doc)
        return doc
