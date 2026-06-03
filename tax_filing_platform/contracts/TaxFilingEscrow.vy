# @version ^0.3.10

"""
TaxFilingEscrow handles payment, order registration, refunds, and public status tracking only.
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
    amount: uint256
    status: uint8
    created_at: uint256
    refunded: bool

owner: public(address)
operator: public(address)
filing_price: public(uint256)
paused: public(bool)
next_order_id: public(uint256)
orders: public(HashMap[uint256, FilingOrder])
collected_fees: public(uint256)


event FilingPaid:
    order_id: uint256
    user: address
    tax_year: uint256
    data_hash: bytes32
    amount: uint256
    timestamp: uint256


event FilingStatusUpdated:
    order_id: uint256
    old_status: uint8
    new_status: uint8
    updated_by: address
    timestamp: uint256


event FilingRefunded:
    order_id: uint256
    user: address
    amount: uint256
    refunded_by: address
    timestamp: uint256


event PriceUpdated:
    old_price: uint256
    new_price: uint256


event OperatorUpdated:
    old_operator: address
    new_operator: address


event Paused:
    by: address


event Unpaused:
    by: address


@external
def __init__(_filing_price: uint256, _operator: address):
    assert _filing_price > 0, "price required"
    assert _operator != empty(address), "operator required"
    self.owner = msg.sender
    self.operator = _operator
    self.filing_price = _filing_price
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
    assert not self.paused, "paused"
    assert msg.value == self.filing_price, "exact price required"
    assert data_hash != empty(bytes32), "hash required"
    assert tax_year >= 2000 and tax_year <= 2100, "invalid tax year"

    order_id: uint256 = self.next_order_id
    self.next_order_id = order_id + 1
    self.orders[order_id] = FilingOrder({
        user: msg.sender,
        tax_year: tax_year,
        data_hash: data_hash,
        amount: msg.value,
        status: PAID,
        created_at: block.timestamp,
        refunded: False
    })
    self.collected_fees += msg.value
    log FilingPaid(order_id, msg.sender, tax_year, data_hash, msg.value, block.timestamp)
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
def refund(order_id: uint256):
    self._only_operator_or_owner()
    assert self._order_exists(order_id), "order missing"
    old_status: uint8 = self.orders[order_id].status
    assert old_status == PAID or old_status == DOCUMENTS_RECEIVED or old_status == IN_REVIEW, "refund forbidden"
    assert not self.orders[order_id].refunded, "already refunded"

    amount: uint256 = self.orders[order_id].amount
    user: address = self.orders[order_id].user
    self.orders[order_id].refunded = True
    self.orders[order_id].status = REFUNDED
    self.collected_fees -= amount
    send(user, amount)
    log FilingRefunded(order_id, user, amount, msg.sender, block.timestamp)
    log FilingStatusUpdated(order_id, old_status, REFUNDED, msg.sender, block.timestamp)


@external
@nonreentrant("escrow")
def withdraw_platform_fees():
    self._only_owner()
    amount: uint256 = self.collected_fees
    assert amount > 0, "no fees"
    self.collected_fees = 0
    send(self.owner, amount)


@external
def set_price(new_price: uint256):
    self._only_owner()
    assert new_price > 0, "price required"
    old_price: uint256 = self.filing_price
    self.filing_price = new_price
    log PriceUpdated(old_price, new_price)


@external
def set_operator(new_operator: address):
    self._only_owner()
    assert new_operator != empty(address), "operator required"
    old_operator: address = self.operator
    self.operator = new_operator
    log OperatorUpdated(old_operator, new_operator)


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
