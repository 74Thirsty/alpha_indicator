# Deployment

1. Generate strong `JWT_SECRET` and base64 encoded 32-byte `MASTER_KEY_B64`.
2. Configure PostgreSQL, Redis, object storage, and Ethereum RPC endpoint.
3. Run `make migrate`.
4. Deploy `TaxFilingEscrow.vy` with audited tooling and a secured deployer key.
5. Configure `ESCROW_CONTRACT_ADDRESS` and operator signing infrastructure.
6. Configure production e-file provider only after IRS/provider approval.
7. Run the backend and worker services behind TLS and a WAF/rate limiter.
