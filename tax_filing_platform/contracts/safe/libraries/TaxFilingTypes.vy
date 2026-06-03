# @version ^0.3.10

"""
Shared Tax Filing Safe Module constants.

Vyper does not currently provide a Solidity-style library linking model for these
simple values, so the module duplicates the constants it needs at compile time.
This file documents the canonical status and operation values used by the Safe
module and guard contracts.
"""

STATUS_NONE: constant(uint8) = 0
AUTHORIZED: constant(uint8) = 1
SETTLED: constant(uint8) = 2
TIMEOUT_REFUNDED: constant(uint8) = 3
CANCELLED: constant(uint8) = 4

SAFE_OPERATION_CALL: constant(uint8) = 0
SAFE_OPERATION_DELEGATECALL: constant(uint8) = 1
