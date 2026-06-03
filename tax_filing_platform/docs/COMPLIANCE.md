# Compliance Boundary

The smart contract does not prepare, sign, transmit, or file tax returns. It only handles payment escrow, order registration, refunds, and status tracking.

Real IRS e-filing requires an authorized IRS e-file provider or approved partner integration. IRS public guidance states that becoming an authorized e-file provider requires completing an application and suitability checks, and the MeF program provides the electronic filing infrastructure for transmitting and receiving return data and acknowledgements.

`ProductionEFileProvider` is intentionally a strict adapter shell. It refuses to initialize without configured production provider credentials and raises `NotImplementedError` until a real approved provider API contract, schemas, credentials, and acknowledgement semantics are implemented.
