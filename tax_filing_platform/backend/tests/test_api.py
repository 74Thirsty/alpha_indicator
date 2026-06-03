def _token(client, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_user_can_register_login_create_filing_and_upload_document(client, tmp_path) -> None:
    response = client.post("/auth/register", json={"email": "new@example.com", "password": "long-secure-password"})
    assert response.status_code == 201, response.text
    token = _token(client, "new@example.com", "long-secure-password")
    headers = {"Authorization": f"Bearer {token}"}
    filing = client.post("/filings", headers=headers, json={"tax_year": 2025, "data_hash": "0x" + "c" * 64})
    assert filing.status_code == 201, filing.text
    filing_id = filing.json()["id"]
    upload = client.post(
        f"/filings/{filing_id}/documents",
        headers=headers,
        files={"file": ("return.txt", b"safe document", "text/plain")},
    )
    assert upload.status_code == 201, upload.text
    assert len(upload.json()["sha256"]) == 64


def test_api_requires_authentication(client) -> None:
    response = client.get("/filings")
    assert response.status_code == 401


def test_blockchain_webhook_is_idempotent(client) -> None:
    payload = {"tx_hash": "0x" + "d" * 64, "log_index": 0, "order_id": 1, "wallet_address": "0x" + "e" * 40, "amount_wei": 10}
    first = client.post("/webhooks/blockchain", json=payload)
    second = client.post("/webhooks/blockchain", json=payload)
    assert first.status_code == 202, first.text
    assert second.status_code == 202, second.text
    assert first.json()["event_id"] == second.json()["event_id"]
