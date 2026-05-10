from datetime import date, datetime, timezone


def calculate_overdue_days(due_date: date, as_of: datetime | None = None) -> int:
    if as_of is None:
        as_of = datetime.now(timezone.utc)
    as_of_date = as_of.date()
    delta_days = (as_of_date - due_date).days
    return max(delta_days, 0)


def is_invoice_overdue(due_date: date, as_of: datetime | None = None) -> bool:
    return calculate_overdue_days(due_date, as_of=as_of) > 0
