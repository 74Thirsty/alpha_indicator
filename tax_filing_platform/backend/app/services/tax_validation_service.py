from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    findings: list[str]


class TaxValidationService:
    def scan_for_malware(self, data: bytes) -> ValidationResult:
        signatures = [b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"]
        if any(sig in data for sig in signatures):
            return ValidationResult(False, ["malware signature detected"])
        return ValidationResult(True, [])

    def validate_tax_document(self, filename: str, data: bytes) -> ValidationResult:
        if not data:
            return ValidationResult(False, ["document is empty"])
        scan = self.scan_for_malware(data)
        if not scan.accepted:
            return scan
        if filename.lower().endswith(".pdf") and not data.startswith(b"%PDF"):
            return ValidationResult(False, ["pdf upload does not contain a PDF header"])
        return ValidationResult(True, [])
