// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title TaxFilingSafeModuleProxy
/// @notice Safe-enabled EIP-1967 proxy for TaxFilingSafeModule implementations.
/// @dev Tax Safes enable this proxy address once. Governance upgrades the
///      implementation behind the same enabled module address. Hot executors and
///      settlement signers have no upgrade authority unless governance makes
///      them the proxy admin, which production deployments must not do.
contract TaxFilingSafeModuleProxy {
    // bytes32(uint256(keccak256("eip1967.proxy.implementation")) - 1)
    bytes32 private constant IMPLEMENTATION_SLOT =
        0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;

    // bytes32(uint256(keccak256("eip1967.proxy.admin")) - 1)
    bytes32 private constant ADMIN_SLOT =
        0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;

    event ProxyInitialized(address indexed governanceAdmin, address indexed implementation);
    event ModuleImplementationUpgraded(
        address indexed oldImplementation,
        address indexed newImplementation,
        address indexed upgradedBy
    );

    constructor(address governanceAdmin, address initialImplementation, bytes memory initCalldata) payable {
        require(governanceAdmin != address(0), "governance required");
        require(initialImplementation != address(0), "implementation required");

        _setAdmin(governanceAdmin);
        _setImplementation(initialImplementation);

        require(initCalldata.length > 0, "initializer required");
        (bool ok, bytes memory returndata) = initialImplementation.delegatecall(initCalldata);
        _verifyCallResult(ok, returndata, "initialization failed");
        require(_moduleOwner() == governanceAdmin, "admin mismatch");

        emit ProxyInitialized(governanceAdmin, initialImplementation);
    }

    modifier onlyGovernanceAdmin() {
        require(msg.sender == admin(), "governance only");
        _;
    }

    function admin() public view returns (address governanceAdmin) {
        bytes32 slot = ADMIN_SLOT;
        assembly {
            governanceAdmin := sload(slot)
        }
    }

    function implementation() public view returns (address activeImplementation) {
        bytes32 slot = IMPLEMENTATION_SLOT;
        assembly {
            activeImplementation := sload(slot)
        }
    }

    function _moduleOwner() private view returns (address moduleOwner) {
        // TaxFilingSafeModule.owner is the first implementation storage slot.
        assembly {
            moduleOwner := sload(0)
        }
    }

    function upgradeTo(address newImplementation) external onlyGovernanceAdmin {
        require(newImplementation != address(0), "implementation required");
        address oldImplementation = implementation();
        require(newImplementation != oldImplementation, "same implementation");
        _setImplementation(newImplementation);
        emit ModuleImplementationUpgraded(oldImplementation, newImplementation, msg.sender);
    }

    function _setAdmin(address newAdmin) private {
        bytes32 slot = ADMIN_SLOT;
        assembly {
            sstore(slot, newAdmin)
        }
    }

    function _setImplementation(address newImplementation) private {
        bytes32 slot = IMPLEMENTATION_SLOT;
        assembly {
            sstore(slot, newImplementation)
        }
    }

    function _delegate(address target) private {
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), target, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch result
            case 0 {
                revert(0, returndatasize())
            }
            default {
                return(0, returndatasize())
            }
        }
    }

    function _verifyCallResult(bool ok, bytes memory returndata, string memory fallbackMessage) private pure {
        if (ok) {
            return;
        }
        if (returndata.length > 0) {
            assembly {
                revert(add(returndata, 0x20), mload(returndata))
            }
        }
        revert(fallbackMessage);
    }

    fallback() external payable {
        _delegate(implementation());
    }

    receive() external payable {
        _delegate(implementation());
    }
}
