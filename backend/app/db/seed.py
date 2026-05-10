from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal  # noqa: E402
from app.services.invoice_service import create_invoice  # noqa: E402
from app.services.seed_data import build_seed_invoices  # noqa: E402
from app.utils.exceptions import DuplicateInvoiceError  # noqa: E402


def seed() -> int:
    created = 0
    db = SessionLocal()
    try:
        for invoice in build_seed_invoices():
            try:
                create_invoice(db, invoice)
                created += 1
            except DuplicateInvoiceError:
                continue
    finally:
        db.close()
    return created


if __name__ == "__main__":
    total = seed()
    print(f"Seeded {total} invoices")
