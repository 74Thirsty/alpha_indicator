# Architecture

The platform separates payment/order metadata from tax preparation. `contracts/TaxFilingEscrow.vy` stores only order IDs, wallet addresses, payment amount, tax year, timestamps, data hashes, and statuses. The backend stores encrypted off-chain documents and workflow records.

Components:

- **FastAPI backend**: authentication, filings, documents, admin workflow, blockchain webhooks.
- **PostgreSQL**: users, filings, documents, payments, audit logs, blockchain events, admin actions.
- **Workers**: blockchain event listener, filing processor, status reconciler.
- **Vyper contract**: payment escrow, status tracking, refunds, fee withdrawal, pause controls.
- **Provider integrations**: mock provider for tests; production provider shell blocked until authorized credentials exist.
