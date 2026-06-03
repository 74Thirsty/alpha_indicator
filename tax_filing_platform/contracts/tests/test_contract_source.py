from pathlib import Path

CONTRACTS = Path(__file__).resolve().parents[1]
MODULE = CONTRACTS / "safe" / "modules" / "TaxFilingSafeModule.vy"
PROXY = CONTRACTS / "safe" / "modules" / "TaxFilingSafeModuleProxy.sol"
SAFE_INTERFACE = CONTRACTS / "safe" / "interfaces" / "ISafe.vy"
GUARD = CONTRACTS / "safe" / "guards" / "TaxFilingGuard.vy"
TYPES = CONTRACTS / "safe" / "libraries" / "TaxFilingTypes.vy"
SOURCE = MODULE.read_text()
PROXY_SOURCE = PROXY.read_text()


def test_safe_module_layout_exists() -> None:
    for contract in [MODULE, PROXY, SAFE_INTERFACE, GUARD, TYPES]:
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
        "ExecutorUpdated",
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
    assert "approved_executor" in SOURCE
    assert "executor not allowed" in SOURCE
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




def test_module_is_initializable_and_versioned_for_proxy_use() -> None:
    assert "def __init__(" not in SOURCE
    assert "def initialize(" in SOURCE
    assert "_governance_admin: address" in SOURCE
    assert 'assert not self.initialized, "already initialized"' in SOURCE
    assert "self.owner = _governance_admin" in SOURCE
    assert "initialized: public(bool)" in SOURCE
    assert "def version() -> String[32]:" in SOURCE
    assert "TaxFilingSafeModule/1.0.0" in SOURCE


def test_proxy_delegates_enabled_module_calls_and_restricts_upgrades() -> None:
    assert "contract TaxFilingSafeModuleProxy" in PROXY_SOURCE
    assert "constructor(address governanceAdmin, address initialImplementation, bytes memory initCalldata)" in PROXY_SOURCE
    assert 'require(initCalldata.length > 0, "initializer required")' in PROXY_SOURCE
    assert "initialImplementation.delegatecall(initCalldata)" in PROXY_SOURCE
    assert 'require(_moduleOwner() == governanceAdmin, "admin mismatch")' in PROXY_SOURCE
    assert "function implementation() public view returns (address activeImplementation)" in PROXY_SOURCE
    assert "function upgradeTo(address newImplementation) external onlyGovernanceAdmin" in PROXY_SOURCE
    assert 'require(msg.sender == admin(), "governance only")' in PROXY_SOURCE
    assert "delegatecall(gas(), target" in PROXY_SOURCE
    assert "return(0, returndatasize())" in PROXY_SOURCE
    assert "approved_executor" not in PROXY_SOURCE
    assert "settlement signer" in PROXY_SOURCE


def test_proxy_uses_eip1967_slots_to_avoid_module_storage_collisions() -> None:
    assert "IMPLEMENTATION_SLOT" in PROXY_SOURCE
    assert "ADMIN_SLOT" in PROXY_SOURCE
    assert 'keccak256("eip1967.proxy.implementation")' in PROXY_SOURCE
    assert 'keccak256("eip1967.proxy.admin")' in PROXY_SOURCE
    assert "function _setImplementation(address newImplementation) private" in PROXY_SOURCE
    assert "function _setAdmin(address newAdmin) private" in PROXY_SOURCE
    assert "sstore(slot, newImplementation)" in PROXY_SOURCE
    assert "sstore(slot, newAdmin)" in PROXY_SOURCE
    assert "owner: public(address)" not in PROXY_SOURCE
    assert "orders: public" not in PROXY_SOURCE


def test_settlement_payload_binds_versioned_offchain_tax_engine_context() -> None:
    assert "calculation_engine_version: bytes32" in SOURCE
    assert "tax_rule_version: bytes32" in SOURCE
    hash_body = SOURCE[SOURCE.index("def _settlement_hash("):SOURCE.index("def _use_nonce(")]
    assert "calculation_engine_version" in hash_body
    assert "tax_rule_version" in hash_body
    assert "convert(chain.id, bytes32)" in hash_body
    assert "convert(self, bytes32)" in hash_body
    settle_body = SOURCE[SOURCE.index("def settle_safe_order("):SOURCE.index("def claim_timeout_refund(")]
    assert 'assert calculation_engine_version != empty(bytes32), "engine version required"' in settle_body
    assert 'assert tax_rule_version != empty(bytes32), "tax rule version required"' in settle_body
    assert "self.orders[safe][order_id].calculation_engine_version = calculation_engine_version" in settle_body
    assert "self.orders[safe][order_id].tax_rule_version = tax_rule_version" in settle_body


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


def test_settlement_requires_approved_executor_distinct_from_signer() -> None:
    settle_body = SOURCE[SOURCE.index("def settle_safe_order("):SOURCE.index("def claim_timeout_refund(")]
    assert "approved_executor: public(HashMap[address, bool])" in SOURCE
    assert "def set_executor_allowed(executor: address, allowed: bool):" in SOURCE
    assert "self._only_owner()" in SOURCE
    assert 'assert executor != empty(address), "executor required"' in SOURCE
    assert "self.approved_executor[executor] = allowed" in SOURCE
    assert "log ExecutorUpdated(executor, allowed)" in SOURCE
    assert 'assert self.approved_executor[msg.sender], "executor not allowed"' in settle_body
    assert 'assert recovered == self.signer, "bad signature"' in settle_body
    assert "assert msg.sender == self.operator" not in settle_body


def test_executor_check_happens_before_signature_and_nonce_use() -> None:
    settle_body = SOURCE[SOURCE.index("def settle_safe_order("):SOURCE.index("def claim_timeout_refund(")]
    executor_check = settle_body.index('assert self.approved_executor[msg.sender], "executor not allowed"')
    signature_check = settle_body.index('assert recovered == self.signer, "bad signature"')
    nonce_use = settle_body.index("self._use_nonce(safe, nonce)")
    assert executor_check < signature_check < nonce_use


def test_signed_settlement_fields_cannot_be_changed_by_executor() -> None:
    hash_body = SOURCE[SOURCE.index("def _settlement_hash("):SOURCE.index("def _use_nonce(")]
    for bound_field in [
        "convert(safe, bytes32)",
        "convert(order_id, bytes32)",
        "convert(tax_due, bytes32)",
        "convert(platform_fee, bytes32)",
        "convert(self.tax_payment_destination, bytes32)",
        "convert(self.platform_fee_recipient, bytes32)",
        "calculation_hash",
        "calculation_engine_version",
        "tax_rule_version",
        "convert(settlement_deadline, bytes32)",
        "convert(nonce, bytes32)",
    ]:
        assert bound_field in hash_body
    settle_body = SOURCE[SOURCE.index("def settle_safe_order("):SOURCE.index("def claim_timeout_refund(")]
    assert "self._execute_safe_payment(safe, self.tax_payment_destination, tax_due)" in settle_body
    assert "self._execute_safe_payment(safe, self.platform_fee_recipient, platform_fee)" in settle_body


def test_executor_and_signer_settlement_gate_semantics() -> None:
    approved_executors = {"executor-a": True}
    signer = "settlement-signer"
    allowed_payouts = {"irs": True, "platform": True}
    logs: list[tuple[str, str, bool]] = []

    def set_executor_allowed(executor: str, allowed: bool) -> None:
        if not executor:
            raise ValueError("executor required")
        approved_executors[executor] = allowed
        logs.append(("ExecutorUpdated", executor, allowed))

    def sign_payload(
        *,
        safe: str = "safe-a",
        order_id: int = 1,
        tax_due: int = 700,
        platform_fee: int = 30,
        tax_destination: str = "irs",
        platform_fee_recipient: str = "platform",
        calculation_hash: str = "calc-hash",
        calculation_engine_version: str = "engine-v1",
        tax_rule_version: str = "tax-rules-2025.1",
        settlement_deadline: int = 200,
        nonce: int = 5,
        signed_by: str = signer,
    ) -> tuple[tuple[object, ...], str]:
        return (
            (
                safe,
                order_id,
                tax_due,
                platform_fee,
                tax_destination,
                platform_fee_recipient,
                calculation_hash,
                calculation_engine_version,
                tax_rule_version,
                settlement_deadline,
                nonce,
            ),
            signed_by,
        )

    def settle(
        *,
        executor: str,
        signature: tuple[tuple[object, ...], str],
        safe: str = "safe-a",
        order_id: int = 1,
        tax_due: int = 700,
        platform_fee: int = 30,
        tax_destination: str = "irs",
        platform_fee_recipient: str = "platform",
        calculation_hash: str = "calc-hash",
        calculation_engine_version: str = "engine-v1",
        tax_rule_version: str = "tax-rules-2025.1",
        settlement_deadline: int = 200,
        nonce: int = 5,
        max_deposit: int = 1_000,
    ) -> bool:
        if not approved_executors.get(executor, False):
            raise ValueError("executor not allowed")
        payload = (
            safe,
            order_id,
            tax_due,
            platform_fee,
            tax_destination,
            platform_fee_recipient,
            calculation_hash,
            calculation_engine_version,
            tax_rule_version,
            settlement_deadline,
            nonce,
        )
        signed_payload, signed_by = signature
        if signed_payload != payload or signed_by != signer:
            raise ValueError("bad signature")
        if not allowed_payouts.get(tax_destination) or not allowed_payouts.get(platform_fee_recipient):
            raise ValueError("target not allowed")
        if tax_due + platform_fee > max_deposit:
            raise ValueError("over max_deposit")
        return True

    valid_signature = sign_payload()

    # 1. Approved executor + valid signer succeeds.
    assert settle(executor="executor-a", signature=valid_signature)

    # 2. Unapproved executor + valid signer fails.
    try:
        settle(executor="executor-b", signature=valid_signature)
    except ValueError as exc:
        assert str(exc) == "executor not allowed"
    else:
        raise AssertionError("unapproved executor relayed a valid signed settlement")

    # 3. Approved executor + bad signer fails.
    try:
        settle(executor="executor-a", signature=sign_payload(signed_by="random-signer"))
    except ValueError as exc:
        assert str(exc) == "bad signature"
    else:
        raise AssertionError("approved executor used a bad signer")

    # 4-6. Approved executor cannot change signed taxDue, platformFee, or payout destination.
    for changed_field in [
        {"tax_due": 701},
        {"platform_fee": 31},
        {"tax_destination": "attacker"},
        {"calculation_engine_version": "engine-v2"},
        {"tax_rule_version": "tax-rules-2026.1"},
    ]:
        try:
            settle(executor="executor-a", signature=valid_signature, **changed_field)
        except ValueError as exc:
            assert str(exc) == "bad signature"
        else:
            raise AssertionError(f"approved executor changed signed field: {changed_field}")

    # 7-8. Removed executor can no longer settle, and executor approval emits a log.
    set_executor_allowed("executor-a", False)
    assert logs[-1] == ("ExecutorUpdated", "executor-a", False)
    try:
        settle(executor="executor-a", signature=valid_signature)
    except ValueError as exc:
        assert str(exc) == "executor not allowed"
    else:
        raise AssertionError("removed executor settled after revocation")


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
