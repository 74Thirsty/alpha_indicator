from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    OPERATOR = "operator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class FilingStatus(StrEnum):
    NONE = "NONE"
    PAID = "PAID"
    DOCUMENTS_RECEIVED = "DOCUMENTS_RECEIVED"
    IN_REVIEW = "IN_REVIEW"
    READY_FOR_SIGNATURE = "READY_FOR_SIGNATURE"
    FILED = "FILED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


ACTIVE_STATUSES = {
    FilingStatus.PAID,
    FilingStatus.DOCUMENTS_RECEIVED,
    FilingStatus.IN_REVIEW,
    FilingStatus.READY_FOR_SIGNATURE,
    FilingStatus.FILED,
    FilingStatus.ACCEPTED,
    FilingStatus.REJECTED,
}
