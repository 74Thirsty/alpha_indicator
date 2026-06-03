from app.integrations.irs_efile_provider import MockEFileProvider, ProductionEFileProvider, ProviderStatus
from app.schemas.payment import BlockchainWebhook
from app.services.blockchain_service import BlockchainService


def test_mock_provider_can_simulate_acceptance_and_rejection() -> None:
    provider = MockEFileProvider()
    submission = provider.submit_return(filing_id="filing-1", tax_year=2025, encrypted_document_hashes=["abc"])
    provider.simulate(submission.provider_submission_id, ProviderStatus.ACCEPTED)
    assert provider.check_status(submission.provider_submission_id) == ProviderStatus.ACCEPTED
    provider.handle_rejection(submission.provider_submission_id, "R0000")
    assert provider.check_status(submission.provider_submission_id) == ProviderStatus.REJECTED


def test_production_provider_requires_credentials(monkeypatch) -> None:
    monkeypatch.delenv("PRODUCTION_EFILE_PROVIDER_ID", raising=False)
    try:
        ProductionEFileProvider()
    except RuntimeError as exc:
        assert "blocked" in str(exc).lower()
    else:
        raise AssertionError("expected missing credentials to block production provider")


def test_reconcile_reports_ingested_events(db_session) -> None:
    service = BlockchainService(db_session)
    service.ingest_paid_event(BlockchainWebhook(tx_hash="0x" + "f" * 64, log_index=0, order_id=7, wallet_address="0x" + "1" * 40, amount_wei=99))
    assert service.reconcile()["events_checked"] == 1
