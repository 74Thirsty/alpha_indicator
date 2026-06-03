# Tax Filing Payment + Workflow Platform

Production-oriented monorepo for a tax filing service workflow. The Vyper contract is a tightly permissioned Safe Module: the User Safe / Business Safe remains the asset-holding account, while the module records filing authorizations and executes only exact signed settlements to allowlisted targets. The FastAPI backend handles users, encrypted document uploads, audit logs, blockchain events, and provider workflow orchestration.

## Compliance boundary

This project does **not** claim to file taxes directly with the IRS. Real electronic filing must happen off-chain through an authorized IRS e-file provider or approved filing partner. IRS guidance explains that providers must apply to become authorized and pass suitability checks, and Modernized e-File (MeF) is the IRS electronic filing infrastructure that processes return data using XML-oriented schemas and acknowledgements.

## Quick start

```bash
cp .env.example .env
make install
make test
make run
```

Docker local development:

```bash
cp .env.example .env
docker compose up --build
```

## Core flows

1. Register and authenticate a user.
2. Link a wallet address.
3. Create a backend filing record with a non-sensitive data hash.
4. Enable `TaxFilingSafeModule` on the User Safe / Business Safe and register it with `enable_module_for_safe()`.
5. Create a Safe-owned filing authorization with `create_filing_order_for_safe(tax_year, data_hash, max_deposit)`.
6. Upload encrypted documents through the backend.
7. Backend/operator submits a signed settlement through `settle_safe_order(...)`, including a settlement deadline and per-Safe unordered nonce; the module burns the nonce in `nonce_bitmap` and can only pay exact signed amounts to allowlisted destinations via the Safe.
8. Mock provider tests simulate filed, accepted, and rejected returns.

## Production-readiness checklist

- [x] No tax PII stored on-chain.
- [x] AES-256-GCM per-file encryption with wrapped file keys.
- [x] Authenticated user APIs and role-protected admin APIs.
- [x] Audit logs for critical actions.
- [x] Idempotent blockchain webhook ingestion.
- [x] E-file provider interface with mock implementation.
- [x] Production provider is explicitly blocked until approved credentials and adapter mapping exist.
- [x] PostgreSQL/Redis/local chain Docker topology.
- [x] Pytest coverage for encryption, permissions, status transitions, upload validation, webhooks, reconciliation, and Safe module source requirements.
