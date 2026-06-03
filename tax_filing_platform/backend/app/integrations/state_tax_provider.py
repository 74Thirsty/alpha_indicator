from __future__ import annotations

from abc import ABC, abstractmethod


class StateTaxProvider(ABC):
    @abstractmethod
    def submit_state_return(self, *, filing_id: str, state_code: str) -> str: ...


class BlockedStateTaxProvider(StateTaxProvider):
    def submit_state_return(self, *, filing_id: str, state_code: str) -> str:
        raise NotImplementedError("State filing is blocked until a state-approved provider integration is configured.")
