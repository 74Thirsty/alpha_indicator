from __future__ import annotations

import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import Optional


IMPLEMENTATION_RELATIVE_PATH = Path("safe/modules/TaxFilingSafeModule.vy")
PROXY_RELATIVE_PATH = Path("safe/modules/TaxFilingSafeModuleProxy.sol")


def resolve_contract_paths() -> tuple[Path, Path]:
    """
    Resolve absolute paths to the Vyper implementation and proxy contracts.
    Ensures both files exist and provides actionable errors.
    """
    contracts_root = Path(__file__).resolve().parents[1]
    implementation_path = contracts_root / IMPLEMENTATION_RELATIVE_PATH
    proxy_path = contracts_root / PROXY_RELATIVE_PATH

    for contract_path in [implementation_path, proxy_path]:
        if not contract_path.exists():
            raise FileNotFoundError(
                f"Contract file not found at expected location: {contract_path}\n"
                "Verify your repository structure or adjust the path resolution."
            )

    return implementation_path, proxy_path


def ensure_env(var: str) -> str:
    """
    Ensure a required environment variable is set.
    """
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {var}\n"
            "Deployment keys must NEVER be committed to the repository."
        )
    return value


def detect_toolchain(preferred: Optional[str] = None) -> str:
    """
    Detect which Ethereum toolchain is available locally.
    Supports: ape, boa, web3.py (via Python import).
    """
    if preferred:
        return preferred

    if shutil.which("ape"):
        return "ape"
    if shutil.which("boa"):
        return "boa"

    try:
        import web3  # noqa: F401
        return "web3"
    except ImportError:
        pass

    raise RuntimeError(
        "No supported Ethereum toolchain detected.\n"
        "Install one of: ape, boa, web3.py"
    )


def print_instructions(implementation: Path, proxy: Path, toolchain: str, verbose: bool = False) -> None:
    """
    Print detailed deployment instructions tailored to the detected toolchain.
    """
    logging.info(f"Implementation resolved at: {implementation}")
    logging.info(f"Proxy resolved at: {proxy}")

    if toolchain == "ape":
        logging.info("Detected toolchain: ape")
        print(
            f"""
Ape Deployment Instructions
---------------------------
1. Compile:
       ape compile

2. Deploy the implementation, then the proxy:
       ape deploy {implementation.stem} --network ethereum:local
       ape deploy {proxy.stem} --network ethereum:local

3. Deploy the proxy with constructor args (governance_admin, implementation,
   init_calldata), where init_calldata encodes initialize(governance_admin,
   operator, signer, platform_fee_recipient, tax_payment_destination,
   default_deadline_seconds). Tax Safes should enable only the proxy address as
   their module.

Ensure your deployer key is provided via environment variables such as:
       APE_PRIVATE_KEY
"""
        )

    elif toolchain == "boa":
        logging.info("Detected toolchain: boa")
        print(
            f"""
Boa Deployment Instructions
---------------------------
Example Python REPL deployment:

    import boa

    with open("{implementation}", "r") as f:
        implementation_source = f.read()
    implementation_contract = boa.load_partial(implementation_source)
    implementation = implementation_contract.deploy()

    # Compile and deploy the Solidity EIP-1967 proxy with solc/forge/web3,
    # passing (governance_admin, implementation.address, init_calldata) to its
    # constructor. init_calldata encodes the implementation initializer.

Tax Safes should enable only the deployed proxy address as their module. Future
production upgrades should be submitted by the governance Safe / multisig through
proxy.upgradeTo(new_implementation).

Ensure your private key is injected via environment variables.
"""
        )

    elif toolchain == "web3":
        logging.info("Detected toolchain: web3.py")
        print(
            f"""
web3.py Deployment Instructions
-------------------------------
Example Python deployment script:

    from web3 import Web3
    import json

    w3 = Web3(Web3.HTTPProvider("<your RPC>"))
    acct = w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))

    with open("{implementation}", "r") as f:
        implementation_source = f.read()
    with open("{proxy}", "r") as f:
        proxy_source = f.read()

    # Compile using vyper:
    #   vyper -f combined_json {implementation}
    #   solc --bin --abi {proxy}

    # Then deploy implementation and proxy using web3.py, deploy the proxy with
    # (governance_admin, implementation, init_calldata), and have Tax Safes enable
    # only the proxy address. Governance Safe / multisig later calls
    # proxy.upgradeTo(new_implementation).

Ensure PRIVATE_KEY is set in your environment.
"""
        )

    if verbose:
        print("\nVerbose mode enabled: additional diagnostics printed above.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Robust deployment helper for the upgradeable TaxFilingSafeModule proxy"
    )
    parser.add_argument(
        "--toolchain",
        choices=["ape", "boa", "web3"],
        help="Force a specific toolchain instead of auto-detection",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only validate environment and paths; do not print instructions",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    implementation, proxy = resolve_contract_paths()

    # Validate required environment variables
    ensure_env("PRIVATE_KEY")

    toolchain = detect_toolchain(args.toolchain)

    if not args.dry_run:
        print_instructions(implementation, proxy, toolchain, verbose=args.verbose)

    logging.info("Deployment helper completed successfully.")


if __name__ == "__main__":
    main()
