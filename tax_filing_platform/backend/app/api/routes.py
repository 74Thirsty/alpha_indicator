from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import FilingStatus, UserRole
from ..models.filing import Filing
from ..models.user import User
from ..schemas.document import DocumentOut
from ..schemas.filing import FilingCreate, FilingOut, StatusUpdate
from ..schemas.payment import BlockchainWebhook
from ..schemas.user import Token, UserCreate, UserLogin, UserOut, WalletLink
from ..security.jwt import create_access_token
from ..security.permissions import get_current_user, require_role
from ..services.auth_service import AuthService
from ..services.blockchain_service import BlockchainService
from ..services.document_service import DocumentService
from ..services.filing_service import FilingService, InvalidStatusTransition
from ..services.payment_service import PaymentService

router = APIRouter()


def _get_owned_filing(db: Session, filing_id: str, user: User) -> Filing:
    filing = db.get(Filing, filing_id)
    if not filing or filing.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="filing not found")
    return filing


def _get_any_filing(db: Session, filing_id: str) -> Filing:
    filing = db.get(Filing, filing_id)
    if not filing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="filing not found")
    return filing


@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        return AuthService(db).register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = AuthService(db).authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return Token(access_token=create_access_token(user.id, user.role.value))


@router.post("/wallet/link", response_model=UserOut)
def link_wallet(payload: WalletLink, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    user.wallet_address = payload.wallet_address.lower()
    db.commit()
    db.refresh(user)
    return user


@router.post("/filings", response_model=FilingOut, status_code=201)
def create_filing(payload: FilingCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Filing:
    return FilingService(db).create(user.id, payload)


@router.get("/filings", response_model=list[FilingOut])
def list_filings(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Filing]:
    return db.query(Filing).filter(Filing.user_id == user.id).order_by(Filing.created_at.desc()).all()


@router.get("/filings/{filing_id}", response_model=FilingOut)
def get_filing(filing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Filing:
    return _get_owned_filing(db, filing_id, user)


@router.post("/filings/{filing_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(filing_id: str, file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    filing = _get_owned_filing(db, filing_id, user)
    return await DocumentService(db).upload(filing=filing, user_id=user.id, file=file)


@router.get("/filings/{filing_id}/status")
def filing_status(filing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    filing = _get_owned_filing(db, filing_id, user)
    return {"status": filing.status.value}


@router.post("/filings/{filing_id}/signature-consent", response_model=FilingOut)
def signature_consent(filing_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Filing:
    return FilingService(db).signature_consent(filing=_get_owned_filing(db, filing_id, user), user_id=user.id)


@router.get("/admin/filings", response_model=list[FilingOut])
def admin_list_filings(_admin: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> list[Filing]:
    return db.query(Filing).order_by(Filing.created_at.desc()).all()


@router.get("/admin/filings/{filing_id}", response_model=FilingOut)
def admin_get_filing(filing_id: str, _admin: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> Filing:
    return _get_any_filing(db, filing_id)


@router.post("/admin/filings/{filing_id}/status", response_model=FilingOut)
def admin_update_status(filing_id: str, payload: StatusUpdate, admin: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> Filing:
    try:
        return FilingService(db).update_status(filing=_get_any_filing(db, filing_id), new_status=payload.status, actor_user_id=admin.id, actor_role=admin.role, reason=payload.reason, super_admin_override=payload.super_admin_override)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/admin/filings/{filing_id}/refund", response_model=FilingOut)
def admin_refund(filing_id: str, payload: StatusUpdate, admin: User = Depends(require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> Filing:
    try:
        return PaymentService(db).initiate_refund(filing=_get_any_filing(db, filing_id), admin_user_id=admin.id, admin_role=admin.role, reason=payload.reason, super_admin_override=payload.super_admin_override)
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/admin/filings/{filing_id}/mark-filed", response_model=FilingOut)
def mark_filed(filing_id: str, admin: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> Filing:
    return FilingService(db).update_status(filing=_get_any_filing(db, filing_id), new_status=FilingStatus.FILED, actor_user_id=admin.id, actor_role=admin.role, reason="operator marked filed")


@router.post("/admin/filings/{filing_id}/mark-accepted", response_model=FilingOut)
def mark_accepted(filing_id: str, admin: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> Filing:
    return FilingService(db).update_status(filing=_get_any_filing(db, filing_id), new_status=FilingStatus.ACCEPTED, actor_user_id=admin.id, actor_role=admin.role, reason="official provider acknowledgement accepted")


@router.post("/admin/filings/{filing_id}/mark-rejected", response_model=FilingOut)
def mark_rejected(filing_id: str, admin: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> Filing:
    return FilingService(db).update_status(filing=_get_any_filing(db, filing_id), new_status=FilingStatus.REJECTED, actor_user_id=admin.id, actor_role=admin.role, reason="official provider acknowledgement rejected")


@router.post("/webhooks/blockchain", status_code=202)
def blockchain_webhook(payload: BlockchainWebhook, db: Session = Depends(get_db)) -> dict[str, str]:
    event = BlockchainService(db).ingest_paid_event(payload)
    return {"event_id": event.id}


@router.get("/blockchain/orders/{order_id}")
def blockchain_order(order_id: int, _user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    payment = BlockchainService(db).get_payment_by_order(order_id)
    return {"order_id": order_id, "payment": None if payment is None else {"tx_hash": payment.tx_hash, "amount_wei": payment.amount_wei}}


@router.post("/blockchain/reconcile")
def blockchain_reconcile(_admin: User = Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)) -> dict[str, int]:
    return BlockchainService(db).reconcile()
