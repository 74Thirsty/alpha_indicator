# Architecture

The platform separates Safe-owned payment authorization from tax preparation. The tax filing module is deployed behind `contracts/safe/modules/TaxFilingSafeModuleProxy.sol`, which delegates to the active `contracts/safe/modules/TaxFilingSafeModule.vy` implementation. The user's or business's Safe remains the asset-holding account; the module stores filing orders, verifies backend settlement signatures, and calls the Safe only for exact approved payments to allowlisted destinations.

```text
User Safe / Business Safe
   ↓ enables module once
TaxFilingSafeModuleProxy.sol
   ↓ delegatecall
current TaxFilingSafeModule implementation
   ↓ validates versioned off-chain calculation context
tax law / calculation engine versions (off-chain Python)
```

Components:

- **FastAPI backend**: authentication, filings, documents, admin workflow, blockchain webhooks.
- **PostgreSQL**: users, filings, documents, payments, audit logs, blockchain events, admin actions.
- **Workers**: blockchain event listener, filing processor, status reconciler.
- **Safe module proxy**: the only module address a Tax Safe enables; delegates calls to the current implementation and exposes `upgradeTo` only to the governance/cold admin stored in the EIP-1967 admin slot.
- **Safe module implementation**: Safe-owned order authorization, signed settlement verification, allowlisted Safe payment execution, timeout refund accounting, pause controls, emergency Safe disable registration, and append-only storage for proxy upgrades.
- **Safe guard companion**: `contracts/safe/guards/TaxFilingGuard.vy` provides an emergency pause/allowlist policy anchor for deployments that add a Safe guard path.
- **Provider integrations**: mock provider for tests; production provider shell blocked until authorized credentials exist.

## Safe-first payment model

The Safe module model replaces direct escrow custody:

```text
Escrow contract model:
User sends money to escrow.

Safe module model:
User/Safe keeps custody.
Module gets narrowly limited authority to move exact approved amounts.
```

The proxy module must be enabled on a Safe before it is useful. After the Safe enables the proxy address, the Safe calls `enable_module_for_safe()` through the proxy to register that Safe with the module. Each Safe then creates its own orders through `create_filing_order_for_safe(tax_year, data_hash, max_deposit)`, so the order owner is the Safe address rather than an EOA.

Settlement is submitted by the backend/operator through `settle_safe_order(safe, order_id, tax_due, platform_fee, calculation_hash, calculation_engine_version, tax_rule_version, settlement_deadline, nonce, v, r, s)`. The signed settlement binds the chain, verifying contract (the proxy address observed by the delegated implementation), Safe, order ID, exact payout amounts, current tax destination, current platform fee recipient, calculation hash, calculation engine version, tax rule version, settlement deadline, and unordered nonce. Replay protection is enforced by `nonce_bitmap`, a per-Safe bitmap keyed by nonce word, so independent settlements can use non-sequential nonces without blocking parallel workflows. The module rejects reused nonces before executing payments and can only call `execTransactionFromModule` with empty calldata, `CALL` operation, exact signed values, and allowlisted payment targets.

## Module upgrade flow

Tax law changes do not move tax calculation on-chain. The versioned Python tax engines remain off-chain and produce a calculation hash plus explicit `calculation_engine_version` and `tax_rule_version` values that must be signed into settlement payloads. Upgradeability lets the module evolve authorization, settlement, compliance, and signing rules while Safes continue using the same enabled proxy address.

1. Deploy a new module implementation.
2. Run regression tests proving existing Safe orders still read and settle under their signed version context.
3. Governance Safe / cold-wallet-governed admin calls `upgradeTo(new_implementation)` on the proxy.
4. The proxy points to the new implementation.
5. Existing Safes keep the same enabled module address.
6. New settlements use the new `tax_rule_version` and/or `calculation_engine_version`.
7. Old orders still settle only with signatures that bind their original versioned rule context.

Hot executors cannot upgrade the proxy. Settlement signers cannot upgrade the proxy. Cold master authority may authorize signer rotations via owner-controlled module administration, but production implementation upgrades should go through the governance Safe / multisig.

## Critical module risk warning

Safe modules can execute transactions from a Safe after being enabled, bypassing the Safe's normal owner-signature path for those module executions. This repository therefore treats the module as high-risk infrastructure: it must never expose arbitrary transaction execution, all execution targets must be allowlisted, every payout must match a signed settlement, emergency pause/disable paths must remain available, and the contracts must be independently audited before production use.
