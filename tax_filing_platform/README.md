# Tax Filing Payment + Workflow Platform

Production-oriented monorepo for a tax filing service workflow. The Vyper contract registers paid orders and tracks status; the FastAPI backend handles users, encrypted document uploads, audit logs, blockchain events, and provider workflow orchestration.

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
4. Pay through `TaxFilingEscrow.create_filing_order(tax_year, data_hash)`.
5. Upload encrypted documents through the backend.
6. Operators update workflow status and initiate refunds through role-protected APIs.
7. Mock provider tests simulate filed, accepted, and rejected returns.

## Production-readiness checklist

- [x] No tax PII stored on-chain.
- [x] AES-256-GCM per-file encryption with wrapped file keys.
- [x] Authenticated user APIs and role-protected admin APIs.
- [x] Audit logs for critical actions.
- [x] Idempotent blockchain webhook ingestion.
- [x] E-file provider interface with mock implementation.
- [x] Production provider is explicitly blocked until approved credentials and adapter mapping exist.
- [x] PostgreSQL/Redis/local chain Docker topology.
- [x] Pytest coverage for encryption, permissions, status transitions, upload validation, webhooks, reconciliation, and contract source requirements.
