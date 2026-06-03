from pathlib import Path

CONTRACTS = Path(__file__).resolve().parents[1]
MODULE = CONTRACTS / "safe" / "modules" / "TaxFilingSafeModule.vy"
SAFE_INTERFACE = CONTRACTS / "safe" / "interfaces" / "ISafe.vy"
GUARD = CONTRACTS / "safe" / "guards" / "TaxFilingGuard.vy"
TYPES = CONTRACTS / "safe" / "libraries" / "TaxFilingTypes.vy"
SOURCE = MODULE.read_text()


def test_safe_module_layout_exists() -> None:
    for contract in [MODULE, SAFE_INTERFACE, GUARD, TYPES]:
        assert contract.exists()


def test_safe_interface_exposes_exec_transaction_from_module() -> None:
    interface_source = SAFE_INTERFACE.read_text()
    assert "interface ISafe" in interface_source
    assert "def execTransactionFromModule" in interface_source
    assert "safe_value: uint256" in interface_source
    assert "data: Bytes[4096]" in interface_source
    assert "operation: uint8" in interface_source


def test_module_keeps_sensitive_data_off_chain() -> None:
    forbidden_storage_terms = ["ssn", "w2", "1099", "address_line", "bank_account"]
    lowered = "\n".join(line for line in SOURCE.lower().splitlines() if not line.strip().startswith('"""'))
    assert all(term not in lowered for term in forbidden_storage_terms)
    assert "data_hash: bytes32" in SOURCE


def test_module_exposes_required_safe_entrypoints_and_events() -> None:
    for name in [
        "enable_module_for_safe",
        "create_filing_order_for_safe",
        "settle_safe_order",
        "claim_timeout_refund",
        "disable_module_for_safe",
        "pause",
        "unpause",
    ]:
        assert f"def {name}" in SOURCE
    for event in [
        "SafeModuleRegistered",
        "SafeModuleDisabled",
        "SafeFilingOrderCreated",
        "SafeFilingOrderSettled",
        "SafeFilingTimeoutRefundClaimed",
        "ExecutionTargetAllowlistUpdated",
        "Paused",
        "Unpaused",
    ]:
        assert f"event {event}" in SOURCE


def test_module_is_tightly_permissioned() -> None:
    assert "execTransactionFromModule" in SOURCE
    assert "allowed_execution_target" in SOURCE
    assert "target not allowed" in SOURCE
    assert "operator only" in SOURCE
    assert "safe only" in SOURCE
    assert "bad signature" in SOURCE
    assert "SAFE_OPERATION_CALL" in SOURCE
    assert "b\"\"" in SOURCE
    assert "DELEGATECALL" not in SOURCE.replace("SAFE_OPERATION_DELEGATECALL", "")


def test_module_declares_reentrancy_guards() -> None:
    assert SOURCE.count("@nonreentrant") >= 2


def test_safe_contracts_compile_when_vyper_is_installed() -> None:
    import sys

    if sys.version_info >= (3, 13):
        return
    try:
        import vyper  # type: ignore
    except ModuleNotFoundError:
        return

    for source_path in [SAFE_INTERFACE, MODULE, GUARD, TYPES]:
        vyper.compile_code(source_path.read_text(), output_formats=["abi", "bytecode"])
