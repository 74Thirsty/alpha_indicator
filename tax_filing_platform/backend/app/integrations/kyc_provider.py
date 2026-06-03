from __future__ import annotations

from abc import ABC, abstractmethod


class KYCProvider(ABC):
    @abstractmethod
    def verify_user(self, user_id: str) -> bool: ...


class ManualReviewKYCProvider(KYCProvider):
    def verify_user(self, user_id: str) -> bool:
        return False
