import argparse
import sys
from datetime import date, timedelta
from uuid import uuid4

import requests

STAGE_CASES = [
    ("STAGE_1", 3),
    ("STAGE_2", 10),
    ("STAGE_3", 17),
    ("STAGE_4", 25),
    ("LEGAL_ESCALATION", 35),
]


def create_invoice(base_url: str, invoice_id: str, overdue_days: int) -> None:
    payload = {
        "invoice_id": invoice_id,
        "client_name": f"Smoke Test {invoice_id}",
        "client_email": f"smoke.{invoice_id}@example.com",
        "amount_due": "1250.00",
        "due_date": (date.today() - timedelta(days=overdue_days)).isoformat(),
        "follow_up_count": 0,
    }
    response = requests.post(f"{base_url}/invoices", json=payload, timeout=10)
    response.raise_for_status()


def delete_invoice(base_url: str, invoice_id: str) -> None:
    response = requests.delete(f"{base_url}/invoices/{invoice_id}", timeout=10)
    if response.status_code not in {200, 204, 404}:
        response.raise_for_status()


def fetch_stage(base_url: str, stage: str) -> list[dict]:
    response = requests.get(f"{base_url}/workflows/stage/{stage}", timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_audit_logs(base_url: str, limit: int = 200) -> list[dict]:
    response = requests.get(f"{base_url}/audit", params={"limit": limit}, timeout=10)
    response.raise_for_status()
    return response.json()


def run_smoke_test(base_url: str, cleanup: bool) -> int:
    created = {}
    failures: list[str] = []

    try:
        for stage, overdue_days in STAGE_CASES:
            invoice_id = f"wf-smoke-{stage.lower()}-{uuid4().hex[:8]}"
            create_invoice(base_url, invoice_id, overdue_days)
            created[stage] = invoice_id

        process_response = requests.post(f"{base_url}/workflows/process-overdue", timeout=15)
        process_response.raise_for_status()

        for stage, invoice_id in created.items():
            stage_items = fetch_stage(base_url, stage)
            if not any(item.get("invoice_id") == invoice_id for item in stage_items):
                failures.append(f"Invoice {invoice_id} not found in stage {stage}")

        audit_logs = fetch_audit_logs(base_url)
        for stage, invoice_id in created.items():
            if stage == "STAGE_1":
                continue
            matched = [
                log
                for log in audit_logs
                if log.get("invoice_id") == invoice_id
                and log.get("action_type") == "ESCALATION_STAGE_UPDATE"
            ]
            if not matched:
                failures.append(f"Missing audit log for invoice {invoice_id} in {stage}")
    except requests.RequestException as exc:
        failures.append(f"HTTP error: {exc}")
    finally:
        if cleanup:
            for invoice_id in created.values():
                try:
                    delete_invoice(base_url, invoice_id)
                except requests.RequestException:
                    failures.append(f"Failed to delete invoice {invoice_id}")

    if failures:
        print("Workflow smoke test failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Workflow smoke test passed.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Workflow smoke test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--cleanup", action="store_true", help="Delete test invoices after run")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exit_code = run_smoke_test(args.base_url.rstrip("/"), args.cleanup)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
