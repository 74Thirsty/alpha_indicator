from app.services.tax_validation_service import TaxValidationService


def test_tax_validation_rejects_eicar_signature() -> None:
    result = TaxValidationService().validate_tax_document("bad.txt", b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE")
    assert not result.accepted
