# Compliance Boundary

The smart contract does not prepare, sign, transmit, or file tax returns. It records Safe-owned filing authorizations and, after signed backend settlement, can instruct an enabled Safe to make exact allowlisted payments for platform fees and legally/compliantly supported tax payment destinations.

The Safe module does not custody user funds directly. Funds stay in the User Safe / Business Safe unless an enabled module execution matches a signed settlement and an allowlisted target.

Real IRS e-filing requires an authorized IRS e-file provider or approved partner integration. IRS public guidance states that becoming an authorized e-file provider requires completing an application and suitability checks, and the MeF program provides the electronic filing infrastructure for transmitting and receiving return data and acknowledgements.

`ProductionEFileProvider` is intentionally a strict adapter shell. It refuses to initialize without configured production provider credentials and raises `NotImplementedError` until a real approved provider API contract, schemas, credentials, and acknowledgement semantics are implemented.
