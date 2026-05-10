from app.models.enums import DeliveryStatus


def test_delivery_status_has_expected_values() -> None:
    values = {status.value for status in DeliveryStatus}
    assert "GENERATED" in values
    assert "PENDING_APPROVAL" in values
    assert "APPROVED" in values
    assert "REJECTED" in values
    assert "DRY_RUN_SENT" in values
    assert "SENT" in values
    assert "FAILED" in values
