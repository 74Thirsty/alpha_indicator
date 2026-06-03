# API

User endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /wallet/link`
- `POST /filings`
- `GET /filings`
- `GET /filings/{id}`
- `POST /filings/{id}/documents`
- `GET /filings/{id}/status`
- `POST /filings/{id}/signature-consent`

Admin/operator endpoints:

- `GET /admin/filings`
- `GET /admin/filings/{id}`
- `POST /admin/filings/{id}/status`
- `POST /admin/filings/{id}/refund`
- `POST /admin/filings/{id}/mark-filed`
- `POST /admin/filings/{id}/mark-accepted`
- `POST /admin/filings/{id}/mark-rejected`

Blockchain endpoints:

- `POST /webhooks/blockchain`
- `GET /blockchain/orders/{order_id}`
- `POST /blockchain/reconcile`
