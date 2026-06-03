# @version ^0.3.10

"""
Upgraded TaxFilingEscrow:
- User deposits a max amount.
- Off-chain tax engine computes tax_due + platform_fee and signs the result.
- Contract verifies signature, settles, and refunds leftover.
- If no settlement before deadline, user can reclaim full deposit.
"""

STATUS_NONE: constant(uint8) = 0
PAID: constant(uint8) = 1
DOCUMENTS_RECEIVED: constant(uint8) = 2
IN_REVIEW: constant(uint8) = 3
READY_FOR_SIGNATURE: constant(uint8) = 4
FILED: constant(uint8) = 5
ACCEPTED: constant(uint8) = 6
REJECTED: constant(uint8) = 7
REFUNDED: constant(uint8) = 8
CANCELLED: constant(uint8) = 9

struct FilingOrder:
    user: address
    tax_year: uint256
    data_hash: bytes32
    max_deposit: uint256
    status: uint8
    created_at: uint256
    deadline: uint256
    settled: bool
    tax_due: uint256
    platform_fee: uint256
    calculation_hash: bytes32

owner: public(address)
operator: public(address)
signer: public(address)  # off-chain tax engine signer
paused: public(bool)
next_order_id: public(uint256)
orders: public(HashMap[uint256, FilingOrder])
collected_fees: public(uint256)
default_deadline_seconds: public(uint256)

event FilingPaid:
    order_id: uint256
    user: address
    tax_year: uint256
    data_hash: bytes32
    max_deposit: uint256
    deadline: uint256
    timestamp: uint256

event FilingStatusUpdated:
    order_id: uint256
    old_status: uint8
    new_status: uint8
    updated_by: address
    timestamp: uint256

event FilingSettled:
    order_id: uint256
    user: address
    tax_due: uint256
    platform_fee: uint256
    refund_amount: uint256
    calculation_hash: bytes32
    signer: address
    timestamp: uint256

event FilingTimeoutRefund:
    order_id: uint256
    user: address
    amount: uint256
    timestamp: uint256

event FilingRefunded:
    order_id: uint256
    user: address
    amount: uint256
    refunded_by: address
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
def __init__(_operator: address, _signer: address, _default_deadline_seconds: uint256):
    assert _operator != empty(address), "operator required"
    assert _signer != empty(address), "signer required"
    assert _default_deadline_seconds > 0, "deadline required"
    self.owner = msg.sender
    self.operator = _operator
    self.signer = _signer
    self.default_deadline_seconds = _default_deadline_seconds
    self.next_order_id = 1


@internal
def _only_owner():
    assert msg.sender == self.owner, "owner only"


@internal
def _only_operator_or_owner():
    assert msg.sender == self.owner or msg.sender == self.operator, "operator only"


@internal
def _order_exists(order_id: uint256) -> bool:
    return self.orders[order_id].status != STATUS_NONE


@internal
def _valid_transition(old_status: uint8, new_status: uint8) -> bool:
    if old_status == PAID and (new_status == DOCUMENTS_RECEIVED or new_status == REFUNDED or new_status == CANCELLED):
        return True
    if old_status == DOCUMENTS_RECEIVED and (new_status == IN_REVIEW or new_status == REFUNDED or new_status == CANCELLED):
        return True
    if old_status == IN_REVIEW and (new_status == READY_FOR_SIGNATURE or new_status == REFUNDED or new_status == CANCELLED):
        return True
    if old_status == READY_FOR_SIGNATURE and (new_status == FILED or new_status == CANCELLED):
        return True
    if old_status == FILED and (new_status == ACCEPTED or new_status == REJECTED):
        return True
    if old_status == REJECTED and new_status == IN_REVIEW:
        return True
    return False


@external
@payable
@nonreentrant("escrow")
def create_filing_order(tax_year: uint256, data_hash: bytes32) -> uint256:
    """
    User deposits a max amount (msg.value) that will later be split into:
    - tax_due
    - platform_fee
    - refund back to user
    """
    assert not self.paused, "paused"
    assert msg.value > 0, "deposit required"
    assert data_hash != empty(bytes32), "hash required"
    assert tax_year >= 2000 and tax_year <= 2100, "invalid tax year"

    order_id: uint256 = self.next_order_id
    self.next_order_id = order_id + 1

    deadline: uint256 = block.timestamp + self.default_deadline_seconds

    self.orders[order_id] = FilingOrder({
        user: msg.sender,
        tax_year: tax_year,
        data_hash: data_hash,
        max_deposit: msg.value,
        status: PAID,
        created_at: block.timestamp,
        deadline: deadline,
        settled: False,
        tax_due: 0,
        platform_fee: 0,
        calculation_hash: empty(bytes32)
    })

    log FilingPaid(order_id, msg.sender, tax_year, data_hash, msg.value, deadline, block.timestamp)
    return order_id


@external
def update_status(order_id: uint256, status: uint8):
    self._only_operator_or_owner()
    assert not self.paused, "paused"
    assert self._order_exists(order_id), "order missing"
    old_status: uint8 = self.orders[order_id].status
    assert self._valid_transition(old_status, status), "invalid transition"
    self.orders[order_id].status = status
    log FilingStatusUpdated(order_id, old_status, status, msg.sender, block.timestamp)


@external
@nonreentrant("escrow")
def settle_order(
    order_id: uint256,
    tax_due: uint256,
    platform_fee: uint256,
    calculation_hash: bytes32,
    v: uint8,
    r: bytes32,
    s: bytes32
):
    """
    Settles an order against a signed off-chain tax calculation.
    - Verifies signature from self.signer.
    - Ensures tax_due + platform_fee <= max_deposit.
    - Moves platform_fee to collected_fees.
    - Refunds leftover to user.
    """
    assert self._order_exists(order_id), "order missing"
    assert not self.paused, "paused"

    order: FilingOrder = self.orders[order_id]
    assert not order.settled, "already settled"
    assert block.timestamp <= order.deadline, "deadline passed"

    total: uint256 = tax_due + platform_fee
    assert total <= order.max_deposit, "over max_deposit"

    # Build message hash: keccak256(order_id, tax_due, platform_fee, calculation_hash)
    msg_hash: bytes32 = keccak256(
        concat(
            convert(order_id, bytes32),
            convert(tax_due, bytes32),
            convert(platform_fee, bytes32),
            calculation_hash
        )
    )
    recovered: address = ecrecover(msg_hash, v, r, s)
    assert recovered == self.signer, "bad signature"

    # Update order
    self.orders[order_id].tax_due = tax_due
    self.orders[order_id].platform_fee = platform_fee
    self.orders[order_id].calculation_hash = calculation_hash
    self.orders[order_id].settled = True
    # You can choose a final status; here we mark as FILED
    old_status: uint8 = self.orders[order_id].status
    self.orders[order_id].status = FILED

    # Accounting
    self.collected_fees += platform_fee

    refund_amount: uint256 = order.max_deposit - total
    if refund_amount > 0:
        send(order.user, refund_amount)

    log FilingSettled(
        order_id,
        order.user,
        tax_due,
        platform_fee,
        refund_amount,
        calculation_hash,
        recovered,
        block.timestamp
    )
    log FilingStatusUpdated(order_id, old_status, FILED, msg.sender, block.timestamp)


@external
@nonreentrant("escrow")
def claim_timeout_refund(order_id: uint256):
    """
    If no settlement happens before deadline, user can reclaim full deposit.
    """
    assert self._order_exists(order_id), "order missing"
    order: FilingOrder = self.orders[order_id]
    assert not order.settled, "already settled"
    assert block.timestamp > order.deadline, "not expired"

    amount: uint256 = order.max_deposit
    self.orders[order_id].settled = True
    self.orders[order_id].status = REFUNDED

    send(order.user, amount)
    log FilingTimeoutRefund(order_id, order.user, amount, block.timestamp)
    # Also emit status update
    log FilingStatusUpdated(order_id, PAID, REFUNDED, msg.sender, block.timestamp)


@external
@nonreentrant("escrow")
def operator_refund(order_id: uint256):
    """
    Optional manual refund path for operator/owner before settlement.
    Refunds full max_deposit to user.
    """
    self._only_operator_or_owner()
    assert self._order_exists(order_id), "order missing"
    order: FilingOrder = self.orders[order_id]
    assert not order.settled, "already settled"

    amount: uint256 = order.max_deposit
    self.orders[order_id].settled = True
    self.orders[order_id].status = REFUNDED

    send(order.user, amount)
    log FilingRefunded(order_id, order.user, amount, msg.sender, block.timestamp)
    log FilingStatusUpdated(order_id, order.status, REFUNDED, msg.sender, block.timestamp)


@external
@nonreentrant("escrow")
def withdraw_platform_fees():
    self._only_owner()
    amount: uint256 = self.collected_fees
    assert amount > 0, "no fees"
    self.collected_fees = 0
    send(self.owner, amount)


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
