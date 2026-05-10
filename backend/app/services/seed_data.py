from datetime import date, timedelta

from app.models.schemas import CreateInvoiceRequest


def build_seed_invoices() -> list[CreateInvoiceRequest]:
    today = date.today()
    return [
        CreateInvoiceRequest(
            invoice_id="INV-1001",
            client_name="Apex Manufacturing",
            client_email="billing@apexmfg.com",
            amount_due=1250.00,
            due_date=today - timedelta(days=15),
            follow_up_count=1,
        ),
        CreateInvoiceRequest(
            invoice_id="INV-1002",
            client_name="Northwind Traders",
            client_email="ap@northwind.com",
            amount_due=5400.00,
            due_date=today + timedelta(days=10),
            follow_up_count=0,
        ),
        CreateInvoiceRequest(
            invoice_id="INV-1003",
            client_name="Contoso Retail",
            client_email="finance@contoso.com",
            amount_due=980.00,
            due_date=today - timedelta(days=35),
            follow_up_count=3,
        ),
    ]
