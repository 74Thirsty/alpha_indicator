# Security

- Never store SSNs, tax forms, income, bank information, addresses, or signatures on-chain.
- Document uploads are validated for size, type, and malware hook result before encryption.
- Each file receives a random AES-256-GCM data key. The data key is wrapped by an environment-provided 32-byte AES-GCM master key.
- APIs use JWT authentication; admin actions require operator/admin/super-admin roles.
- Critical actions create audit records.
- Blockchain webhooks are idempotent on `(tx_hash, log_index)`.
- Secrets and private keys belong in the environment only.
