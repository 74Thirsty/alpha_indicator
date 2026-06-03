# @version ^0.3.10

"""
TaxFilingSafeModule

Safe-first filing settlement module. The Safe remains the asset-holding account;
this module stores filing authorizations and can only ask an enabled Safe to send
exact, signed settlement payments to allowlisted recipients.

WARNING: Safe modules bypass the Safe owner signature flow once enabled. This
module must be treated as high-risk infrastructure and audited before production.
"""

interface ISafe:
    def execTransactionFromModule(
        to: address,
        safe_value: uint256,
        data: Bytes[4096],
        operation: uint8
    ) -> bool: nonpayable

STATUS_NONE: constant(uint8) = 0
AUTHORIZED: constant(uint8) = 1
SETTLED: constant(uint8) = 2
TIMEOUT_REFUNDED: constant(uint8) = 3
CANCELLED: constant(uint8) = 4

SAFE_OPERATION_CALL: constant(uint8) = 0

struct SafeFilingOrder:
    safe: address
    tax_year: uint256
    data_hash: bytes32
    max_deposit: uint256
    status: uint8
    created_at: uint256
    deadline: uint256
    settled: bool
    tax_due: uint256
    platform_fee: uint256
    refund_amount: uint256
    calculation_hash: bytes32

owner: public(address)
operator: public(address)
signer: public(address)
platform_fee_recipient: public(address)
tax_payment_destination: public(address)
paused: public(bool)
default_deadline_seconds: public(uint256)

safe_enabled: public(HashMap[address, bool])
next_order_id_by_safe: public(HashMap[address, uint256])
orders: public(HashMap[address, HashMap[uint256, SafeFilingOrder]])
allowed_execution_target: public(HashMap[address, bool])

used_settlement_hash: public(HashMap[bytes32, bool])


event SafeModuleRegistered:
    safe: indexed(address)
    registered_by: address
    timestamp: uint256


event SafeModuleDisabled:
    safe: indexed(address)
    disabled_by: address
    timestamp: uint256


event ExecutionTargetAllowlistUpdated:
    target: indexed(address)
    allowed: bool


event PlatformFeeRecipientUpdated:
    old_recipient: address
    new_recipient: address


event TaxPaymentDestinationUpdated:
    old_destination: address
    new_destination: address


event SafeFilingOrderCreated:
    safe: indexed(address)
    order_id: indexed(uint256)
    tax_year: uint256
    data_hash: bytes32
    max_deposit: uint256
    deadline: uint256
    timestamp: uint256


event SafeFilingOrderSettled:
    safe: indexed(address)
    order_id: indexed(uint256)
    tax_due: uint256
    platform_fee: uint256
    refund_amount: uint256
    tax_destination: address
    platform_fee_recipient: address
    calculation_hash: bytes32
    settlement_hash: bytes32
    timestamp: uint256


event SafeFilingTimeoutRefundClaimed:
    safe: indexed(address)
    order_id: indexed(uint256)
    refund_amount: uint256
    timestamp: uint256


event OperatorUpdated:
    old_operator: address
    new_operator: address


event SignerUpdated:
    old_signer: address
    new_signer: address


event DeadlineUpdated:
    old_deadline: uint256
    new_deadline: uint256


event Paused:
    by: address


event Unpaused:
    by: address


@external
def __init__(
    _operator: address,
    _signer: address,
    _platform_fee_recipient: address,
    _tax_payment_destination: address,
    _default_deadline_seconds: uint256
):
    assert _operator != empty(address), "operator required"
    assert _signer != empty(address), "signer required"
    assert _platform_fee_recipient != empty(address), "fee recipient required"
    assert _tax_payment_destination != empty(address), "tax destination required"
    assert _default_deadline_seconds > 0, "deadline required"

    self.owner = msg.sender
    self.operator = _operator
    self.signer = _signer
    self.platform_fee_recipient = _platform_fee_recipient
    self.tax_payment_destination = _tax_payment_destination
    self.default_deadline_seconds = _default_deadline_seconds
    self.allowed_execution_target[_platform_fee_recipient] = True
    self.allowed_execution_target[_tax_payment_destination] = True


@internal
def _only_owner():
    assert msg.sender == self.owner, "owner only"


@internal
def _only_operator_or_owner():
    assert msg.sender == self.owner or msg.sender == self.operator, "operator only"


@internal
def _only_enabled_safe(safe: address):
    assert msg.sender == safe, "safe only"
    assert self.safe_enabled[safe], "safe not registered"


@internal
def _order_exists(safe: address, order_id: uint256) -> bool:
    return self.orders[safe][order_id].status != STATUS_NONE


@internal
def _settlement_hash(
    safe: address,
    order_id: uint256,
    tax_due: uint256,
    platform_fee: uint256,
    calculation_hash: bytes32
) -> bytes32:
    return keccak256(
        concat(
            convert(chain.id, bytes32),
            convert(self, bytes32),
            convert(safe, bytes32),
            convert(order_id, bytes32),
            convert(tax_due, bytes32),
            convert(platform_fee, bytes32),
            convert(self.tax_payment_destination, bytes32),
            convert(self.platform_fee_recipient, bytes32),
            calculation_hash
        )
    )


@internal
def _execute_safe_payment(safe: address, target: address, amount: uint256):
    if amount == 0:
        return
    assert target != empty(address), "target required"
    assert self.allowed_execution_target[target], "target not allowed"
    ok: bool = ISafe(safe).execTransactionFromModule(target, amount, b"", SAFE_OPERATION_CALL)
    assert ok, "safe execution failed"


@external
def enable_module_for_safe():
    """
    Safe must call this after enabling this contract as a Safe module.
    This local registration lets user-facing functions verify msg.sender is the
    Safe and prevents EOAs or unrelated contracts from creating orders for it.
    """
    assert not self.paused, "paused"
    assert msg.sender != empty(address), "safe required"
    self.safe_enabled[msg.sender] = True
    if self.next_order_id_by_safe[msg.sender] == 0:
        self.next_order_id_by_safe[msg.sender] = 1
    log SafeModuleRegistered(msg.sender, msg.sender, block.timestamp)


@external
def disable_module_for_safe(safe: address):
    """
    Emergency disable path. A Safe can disable itself; the owner/operator can
    also disable a Safe during incident response. The Safe should also remove
    this module from its own Safe module list.
    """
    assert msg.sender == safe or msg.sender == self.owner or msg.sender == self.operator, "not authorized"
    self.safe_enabled[safe] = False
    log SafeModuleDisabled(safe, msg.sender, block.timestamp)


@external
def create_filing_order_for_safe(tax_year: uint256, data_hash: bytes32, max_deposit: uint256) -> uint256:
    self._only_enabled_safe(msg.sender)
    assert not self.paused, "paused"
    assert data_hash != empty(bytes32), "hash required"
    assert tax_year >= 2000 and tax_year <= 2100, "invalid tax year"
    assert max_deposit > 0, "max deposit required"

    order_id: uint256 = self.next_order_id_by_safe[msg.sender]
    self.next_order_id_by_safe[msg.sender] = order_id + 1
    deadline: uint256 = block.timestamp + self.default_deadline_seconds

    self.orders[msg.sender][order_id] = SafeFilingOrder({
        safe: msg.sender,
        tax_year: tax_year,
        data_hash: data_hash,
        max_deposit: max_deposit,
        status: AUTHORIZED,
        created_at: block.timestamp,
        deadline: deadline,
        settled: False,
        tax_due: 0,
        platform_fee: 0,
        refund_amount: 0,
        calculation_hash: empty(bytes32)
    })

    log SafeFilingOrderCreated(msg.sender, order_id, tax_year, data_hash, max_deposit, deadline, block.timestamp)
    return order_id


@external
@nonreentrant("module")
def settle_safe_order(
    safe: address,
    order_id: uint256,
    tax_due: uint256,
    platform_fee: uint256,
    calculation_hash: bytes32,
    v: uint8,
    r: bytes32,
    s: bytes32
):
    """
    Backend/operator submits a signed settlement. The signature binds this
    module, chain, Safe, order, exact payout amounts, current allowlisted payout
    destinations, and calculation hash.
    """
    assert msg.sender == self.operator, "operator only"
    assert self.safe_enabled[safe], "safe not registered"
    assert self._order_exists(safe, order_id), "order missing"
    assert not self.paused, "paused"

    order: SafeFilingOrder = self.orders[safe][order_id]
    assert order.status == AUTHORIZED, "not authorized"
    assert not order.settled, "already settled"
    assert block.timestamp <= order.deadline, "deadline passed"
    assert calculation_hash != empty(bytes32), "calculation hash required"

    total: uint256 = tax_due + platform_fee
    assert total <= order.max_deposit, "over max_deposit"
    assert self.allowed_execution_target[self.tax_payment_destination], "tax target not allowed"
    assert self.allowed_execution_target[self.platform_fee_recipient], "fee target not allowed"

    digest: bytes32 = self._settlement_hash(safe, order_id, tax_due, platform_fee, calculation_hash)
    assert not self.used_settlement_hash[digest], "settlement used"
    recovered: address = ecrecover(digest, v, r, s)
    assert recovered == self.signer, "bad signature"

    self.used_settlement_hash[digest] = True
    self.orders[safe][order_id].tax_due = tax_due
    self.orders[safe][order_id].platform_fee = platform_fee
    self.orders[safe][order_id].refund_amount = order.max_deposit - total
    self.orders[safe][order_id].calculation_hash = calculation_hash
    self.orders[safe][order_id].settled = True
    self.orders[safe][order_id].status = SETTLED

    self._execute_safe_payment(safe, self.tax_payment_destination, tax_due)
    self._execute_safe_payment(safe, self.platform_fee_recipient, platform_fee)

    log SafeFilingOrderSettled(
        safe,
        order_id,
        tax_due,
        platform_fee,
        order.max_deposit - total,
        self.tax_payment_destination,
        self.platform_fee_recipient,
        calculation_hash,
        digest,
        block.timestamp
    )


@external
@nonreentrant("module")
def claim_timeout_refund(safe: address, order_id: uint256):
    self._only_enabled_safe(safe)
    assert self._order_exists(safe, order_id), "order missing"

    order: SafeFilingOrder = self.orders[safe][order_id]
    assert order.status == AUTHORIZED, "not authorized"
    assert not order.settled, "already settled"
    assert block.timestamp > order.deadline, "not expired"

    self.orders[safe][order_id].settled = True
    self.orders[safe][order_id].status = TIMEOUT_REFUNDED
    self.orders[safe][order_id].refund_amount = order.max_deposit

    # Safe-first model: no funds were escrowed by the module, so the unused
    # authorization remains in the Safe rather than being transferred back.
    log SafeFilingTimeoutRefundClaimed(safe, order_id, order.max_deposit, block.timestamp)


@external
def set_execution_target_allowed(target: address, allowed: bool):
    self._only_owner()
    assert target != empty(address), "target required"
    self.allowed_execution_target[target] = allowed
    log ExecutionTargetAllowlistUpdated(target, allowed)


@external
def set_platform_fee_recipient(new_recipient: address):
    self._only_owner()
    assert new_recipient != empty(address), "fee recipient required"
    assert self.allowed_execution_target[new_recipient], "recipient not allowed"
    old_recipient: address = self.platform_fee_recipient
    self.platform_fee_recipient = new_recipient
    log PlatformFeeRecipientUpdated(old_recipient, new_recipient)


@external
def set_tax_payment_destination(new_destination: address):
    self._only_owner()
    assert new_destination != empty(address), "tax destination required"
    assert self.allowed_execution_target[new_destination], "destination not allowed"
    old_destination: address = self.tax_payment_destination
    self.tax_payment_destination = new_destination
    log TaxPaymentDestinationUpdated(old_destination, new_destination)


@external
def set_operator(new_operator: address):
    self._only_owner()
    assert new_operator != empty(address), "operator required"
    old_operator: address = self.operator
    self.operator = new_operator
    log OperatorUpdated(old_operator, new_operator)


@external
def set_signer(new_signer: address):
    self._only_owner()
    assert new_signer != empty(address), "signer required"
    old_signer: address = self.signer
    self.signer = new_signer
    log SignerUpdated(old_signer, new_signer)


@external
def set_default_deadline_seconds(new_deadline: uint256):
    self._only_owner()
    assert new_deadline > 0, "deadline required"
    old_deadline: uint256 = self.default_deadline_seconds
    self.default_deadline_seconds = new_deadline
    log DeadlineUpdated(old_deadline, new_deadline)


@external
def pause():
    self._only_owner()
    self.paused = True
    log Paused(msg.sender)


@external
def unpause():
    self._only_owner()
    self.paused = False
    log Unpaused(msg.sender)
