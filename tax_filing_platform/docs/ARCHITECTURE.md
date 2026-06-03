# Architecture

The platform separates Safe-owned payment authorization from tax preparation. The tax filing contract is implemented as `contracts/safe/modules/TaxFilingSafeModule.vy`, not as a custody escrow. The user's or business's Safe remains the asset-holding account; the module stores filing orders, verifies backend settlement signatures, and calls the Safe only for exact approved payments to allowlisted destinations.

```text
User Safe / Business Safe
   ↓ enables module
TaxFilingSafeModule.vy
   ↓ executes approved Safe transactions
Tax filing backend / signer
```

Components:

- **FastAPI backend**: authentication, filings, documents, admin workflow, blockchain webhooks.
- **PostgreSQL**: users, filings, documents, payments, audit logs, blockchain events, admin actions.
- **Workers**: blockchain event listener, filing processor, status reconciler.
- **Safe module contract**: Safe-owned order authorization, signed settlement verification, allowlisted Safe payment execution, timeout refund accounting, pause controls, and emergency Safe disable registration.
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

The module must be enabled on a Safe before it is useful. After the Safe enables it, the Safe calls `enable_module_for_safe()` to register that Safe with the module. Each Safe then creates its own orders through `create_filing_order_for_safe(tax_year, data_hash, max_deposit)`, so the order owner is the Safe address rather than an EOA.

Settlement is submitted by the backend/operator through `settle_safe_order(safe, order_id, tax_due, platform_fee, calculation_hash, settlement_deadline, nonce, v, r, s)`. The signed settlement binds the chain, module, Safe, order ID, exact payout amounts, current tax destination, current platform fee recipient, calculation hash, settlement deadline, and unordered nonce. Replay protection is enforced by `nonce_bitmap`, a per-Safe bitmap keyed by nonce word, so independent settlements can use non-sequential nonces without blocking parallel workflows. The module rejects reused nonces before executing payments and can only call `execTransactionFromModule` with empty calldata, `CALL` operation, exact signed values, and allowlisted payment targets.

## Critical module risk warning

Safe modules can execute transactions from a Safe after being enabled, bypassing the Safe's normal owner-signature path for those module executions. This repository therefore treats the module as high-risk infrastructure: it must never expose arbitrary transaction execution, all execution targets must be allowlisted, every payout must match a signed settlement, emergency pause/disable paths must remain available, and the contracts must be independently audited before production use.
