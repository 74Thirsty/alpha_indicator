from app.database import Base


def test_required_tables_are_registered() -> None:
    expected = {"users", "filings", "documents", "payments", "audit_logs", "blockchain_events", "admin_actions"}
    assert expected.issubset(Base.metadata.tables.keys())
