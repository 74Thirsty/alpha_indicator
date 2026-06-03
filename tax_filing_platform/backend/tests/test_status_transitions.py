import pytest

from app.models.enums import FilingStatus, UserRole
from app.models.filing import Filing
from app.services.filing_service import FilingService, InvalidStatusTransition


def test_allowed_refund_transition(db_session, user) -> None:
    filing = Filing(user_id=user.id, tax_year=2025, data_hash="0x" + "a" * 64, status=FilingStatus.PAID)
    db_session.add(filing)
    db_session.commit()
    updated = FilingService(db_session).update_status(filing=filing, new_status=FilingStatus.REFUNDED, actor_user_id=user.id, actor_role=UserRole.ADMIN, reason="customer request")
    assert updated.status == FilingStatus.REFUNDED


def test_disallowed_accepted_refund_without_override(db_session, user) -> None:
    filing = Filing(user_id=user.id, tax_year=2025, data_hash="0x" + "b" * 64, status=FilingStatus.ACCEPTED)
    db_session.add(filing)
    db_session.commit()
    with pytest.raises(InvalidStatusTransition):
        FilingService(db_session).update_status(filing=filing, new_status=FilingStatus.REFUNDED, actor_user_id=user.id, actor_role=UserRole.ADMIN, reason="late refund")
