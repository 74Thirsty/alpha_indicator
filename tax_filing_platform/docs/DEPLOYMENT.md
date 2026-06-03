# Deployment

1. Generate strong `JWT_SECRET` and base64 encoded 32-byte `MASTER_KEY_B64`.
2. Configure PostgreSQL, Redis, object storage, and Ethereum RPC endpoint.
3. Run `make migrate`.
4. Deploy `contracts/safe/modules/TaxFilingSafeModule.vy` with audited tooling and a secured deployer key.
5. Deploy/configure the optional `contracts/safe/guards/TaxFilingGuard.vy` emergency guard path if required for the Safe deployment.
6. Configure the module constructor with the operator, settlement signer, platform fee recipient, authorized tax payment destination, and default deadline.
7. Allowlist every module execution target before it can receive Safe-funded payments.
8. Enable the deployed module on each User Safe / Business Safe, then have that Safe call `enable_module_for_safe()`.
9. Configure backend module addresses, Safe addresses, and operator signing infrastructure.
10. Configure production e-file provider only after IRS/provider approval.
11. Run the backend and worker services behind TLS and a WAF/rate limiter.

Safe modules bypass the Safe's normal owner signature path after being enabled, so deployment must include independent audit, guarded key management, monitoring, and an emergency process to pause the module and disable Safe registrations.
