from datetime import date, datetime, timezone

from app.utils.overdue import calculate_overdue_days, is_invoice_overdue


def test_calculate_overdue_days() -> None:
    as_of = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    assert calculate_overdue_days(date(2026, 5, 9), as_of=as_of) == 1
    assert calculate_overdue_days(date(2026, 5, 10), as_of=as_of) == 0
    assert calculate_overdue_days(date(2026, 5, 11), as_of=as_of) == 0


def test_is_invoice_overdue() -> None:
    as_of = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    assert is_invoice_overdue(date(2026, 5, 1), as_of=as_of) is True
    assert is_invoice_overdue(date(2026, 5, 10), as_of=as_of) is False
