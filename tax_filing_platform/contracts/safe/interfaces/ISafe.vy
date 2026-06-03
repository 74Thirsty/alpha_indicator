# @version ^0.3.10

interface ISafe:
    def execTransactionFromModule(
        to: address,
        safe_value: uint256,
        data: Bytes[4096],
        operation: uint8
    ) -> bool: nonpayable
