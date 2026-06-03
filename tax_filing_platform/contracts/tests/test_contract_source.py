from pathlib import Path

CONTRACT = Path(__file__).resolve().parents[1] / "TaxFilingEscrow.vy"
SOURCE = CONTRACT.read_text()


def test_contract_keeps_sensitive_data_off_chain() -> None:
    forbidden_storage_terms = ["ssn", "w2", "1099", "address_line", "bank_account"]
    lowered = "\n".join(line for line in SOURCE.lower().splitlines() if not line.strip().startswith('"""'))
    assert all(term not in lowered for term in forbidden_storage_terms)
    assert "data_hash: bytes32" in SOURCE


def test_contract_exposes_required_entrypoints_and_events() -> None:
    for name in ["create_filing_order", "update_status", "refund", "withdraw_platform_fees", "pause", "unpause"]:
        assert f"def {name}" in SOURCE
    for event in ["FilingPaid", "FilingStatusUpdated", "FilingRefunded", "PriceUpdated", "OperatorUpdated", "Paused", "Unpaused"]:
        assert f"event {event}" in SOURCE


def test_contract_declares_reentrancy_guards() -> None:
    assert SOURCE.count("@nonreentrant") >= 3


def test_contract_compiles_when_vyper_is_installed() -> None:
    import sys
    if sys.version_info >= (3, 13):
        return
    try:
        import vyper  # type: ignore
    except ModuleNotFoundError:
        return
    vyper.compile_code(SOURCE, output_formats=["abi", "bytecode"])
