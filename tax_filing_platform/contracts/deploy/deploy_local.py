from __future__ import annotations

from pathlib import Path


def main() -> None:
    contract = Path(__file__).resolve().parents[1] / "TaxFilingEscrow.vy"
    print(f"Compile and deploy {contract} with your approved local Ethereum tooling (ape, boa, or web3.py).")
    print("Deployment requires a funded deployer key supplied via environment, never committed to the repository.")


if __name__ == "__main__":
    main()
