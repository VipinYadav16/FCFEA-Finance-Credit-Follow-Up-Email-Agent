import argparse
import sys

import requests


def call(method: str, url: str, **kwargs):
    response = requests.request(method, url, timeout=20, **kwargs)
    response.raise_for_status()
    return response.json() if response.content else {}


def run(base_url: str, invoice_id: str) -> int:
    steps = []
    try:
        steps.append(("workflow_process", call("POST", f"{base_url}/workflows/process-overdue")))
        steps.append(("ai_generate", call("POST", f"{base_url}/ai/generate/{invoice_id}")))
        steps.append(("delivery_approve", call("POST", f"{base_url}/delivery/approve/{invoice_id}")))
        steps.append(("delivery_dry_run", call("POST", f"{base_url}/delivery/dry-run-send/{invoice_id}")))
        steps.append(("orch_run", call("POST", f"{base_url}/orchestration/run/{invoice_id}")))
        steps.append(("orch_trace", call("GET", f"{base_url}/orchestration/trace/{invoice_id}")))
    except requests.RequestException as exc:
        print(f"Final E2E smoke failed: {exc}")
        return 1

    print("Final E2E smoke passed. Steps executed:")
    for name, payload in steps:
        print(f"- {name}: ok")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Final end-to-end smoke script")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--invoice-id", required=True)
    args = parser.parse_args()
    code = run(args.base_url.rstrip("/"), args.invoice_id)
    sys.exit(code)


if __name__ == "__main__":
    main()
