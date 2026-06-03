from __future__ import annotations

import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import Optional


CONTRACT_NAME = "TaxFilingEscrow.vy"


def resolve_contract_path() -> Path:
    """
    Resolve the absolute path to the Vyper contract.
    Ensures the file exists and provides actionable errors.
    """
    contract_path = Path(__file__).resolve().parents[1] / CONTRACT_NAME

    if not contract_path.exists():
        raise FileNotFoundError(
            f"Contract file not found at expected location: {contract_path}\n"
            "Verify your repository structure or adjust the path resolution."
        )

    return contract_path


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


def print_instructions(contract: Path, toolchain: str, verbose: bool = False) -> None:
    """
    Print detailed deployment instructions tailored to the detected toolchain.
    """
    logging.info(f"Contract resolved at: {contract}")

    if toolchain == "ape":
        logging.info("Detected toolchain: ape")
        print(
            f"""
Ape Deployment Instructions
---------------------------
1. Compile:
       ape compile

2. Deploy:
       ape deploy {contract.stem} --network ethereum:local

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

    with open("{contract}", "r") as f:
        source = f.read()

    contract = boa.load_partial(source)
    deployed = contract.deploy(<constructor args>)

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

    with open("{contract}", "r") as f:
        source = f.read()

    # Compile using vyper:
    #   vyper -f combined_json {contract}

    # Then deploy using web3.py

Ensure PRIVATE_KEY is set in your environment.
"""
        )

    if verbose:
        print("\nVerbose mode enabled: additional diagnostics printed above.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Robust deployment helper for TaxFilingEscrow.vy"
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

    contract = resolve_contract_path()

    # Validate required environment variables
    ensure_env("PRIVATE_KEY")

    toolchain = detect_toolchain(args.toolchain)

    if not args.dry_run:
        print_instructions(contract, toolchain, verbose=args.verbose)

    logging.info("Deployment helper completed successfully.")


if __name__ == "__main__":
    main()
