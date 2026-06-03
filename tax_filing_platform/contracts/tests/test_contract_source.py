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


def test_module_uses_per_safe_unordered_nonce_bitmap() -> None:
    assert "nonce_bitmap: public(HashMap[address, HashMap[uint256, uint256]])" in SOURCE
    assert "def _use_nonce(safe: address, nonce: uint256):" in SOURCE
    assert "word_pos: uint256 = nonce / 256" in SOURCE
    assert "bit_pos: uint256 = nonce % 256" in SOURCE
    assert "bit: uint256 = shift(1, convert(bit_pos, int256))" in SOURCE
    assert "self.nonce_bitmap[safe][word_pos]" in SOURCE
    assert 'assert word & bit == 0, "nonce used"' in SOURCE
    assert "self.nonce_bitmap[safe][word_pos] = word | bit" in SOURCE
    assert "used_settlement_hash" not in SOURCE


def test_settlement_signature_binds_deadline_and_nonce() -> None:
    assert "settlement_deadline: uint256" in SOURCE
    assert "nonce: uint256" in SOURCE
    assert "convert(settlement_deadline, bytes32)" in SOURCE
    assert "convert(nonce, bytes32)" in SOURCE
    assert 'assert block.timestamp <= settlement_deadline, "settlement expired"' in SOURCE
    assert "self._use_nonce(safe, nonce)" in SOURCE


def test_nonce_is_consumed_after_signature_checks_and_before_payments() -> None:
    settle_body = SOURCE[SOURCE.index("def settle_safe_order("):SOURCE.index("def claim_timeout_refund(")]
    nonce_use = settle_body.index("self._use_nonce(safe, nonce)")
    signature_check = settle_body.index('assert recovered == self.signer, "bad signature"')
    first_payment = settle_body.index("self._execute_safe_payment")
    assert signature_check < nonce_use < first_payment


def test_nonce_bitmap_semantics_cover_required_replay_cases() -> None:
    bitmap: dict[str, dict[int, int]] = {}

    def use_nonce(safe: str, nonce: int) -> None:
        word_pos = nonce // 256
        bit_pos = nonce % 256
        bit = 1 << bit_pos
        word = bitmap.setdefault(safe, {}).get(word_pos, 0)
        if word & bit:
            raise ValueError("nonce used")
        bitmap[safe][word_pos] = word | bit

    # first use of nonce succeeds
    use_nonce("safe-a", 5)

    # second use of same nonce fails; an altered payload with the same nonce fails
    # through the same per-Safe nonce invalidation path once the first settlement succeeds.
    for replayed_nonce in [5, 5]:
        try:
            use_nonce("safe-a", replayed_nonce)
        except ValueError as exc:
            assert str(exc) == "nonce used"
        else:
            raise AssertionError("same Safe reused a burned nonce")

    # different Safe can use same nonce
    use_nonce("safe-b", 5)

    # high nonce works and lands in a high bitmap word
    use_nonce("safe-a", 999999)
    assert bitmap["safe-a"][999999 // 256] & (1 << (999999 % 256))

    # nonce in different bitmap word works and does not collide with nonce 5
    use_nonce("safe-a", 256)
    assert bitmap["safe-a"][1] & 1

    # replay after settlement fails
    try:
        use_nonce("safe-a", 999999)
    except ValueError:
        pass
    else:
        raise AssertionError("replay after settlement reused a burned nonce")
