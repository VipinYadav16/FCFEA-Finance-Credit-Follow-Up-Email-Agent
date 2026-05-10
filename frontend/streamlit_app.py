import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Finance Credit Follow-Up Email Agent", layout="wide")


def fetch_invoices() -> tuple[list[dict], str | None]:
    try:
        response = requests.get(f"{BACKEND_URL}/invoices", timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return [], str(exc)


def fetch_workflow_overdue() -> tuple[list[dict], str | None]:
    try:
        response = requests.get(f"{BACKEND_URL}/workflows/overdue", timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return [], str(exc)


def fetch_workflow_escalated() -> tuple[list[dict], str | None]:
    try:
        response = requests.get(f"{BACKEND_URL}/workflows/escalated", timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return [], str(exc)


def fetch_workflow_stage(stage: str) -> tuple[list[dict], str | None]:
    try:
        response = requests.get(f"{BACKEND_URL}/workflows/stage/{stage}", timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return [], str(exc)


def fetch_audit_logs(limit: int) -> tuple[list[dict], str | None]:
    try:
        response = requests.get(f"{BACKEND_URL}/audit", params={"limit": limit}, timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return [], str(exc)


def generate_ai_email(invoice_id: str) -> tuple[dict | None, str | None]:
    try:
        response = requests.post(f"{BACKEND_URL}/ai/generate/{invoice_id}", timeout=25)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def fetch_ai_preview(invoice_id: str) -> tuple[dict | None, str | None]:
    try:
        response = requests.get(f"{BACKEND_URL}/ai/generated-preview/{invoice_id}", timeout=10)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def generate_ai_batch(limit: int) -> tuple[dict | None, str | None]:
    try:
        response = requests.post(
            f"{BACKEND_URL}/ai/generate-overdue-batch",
            json={"limit": limit},
            timeout=60,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def render_metrics(invoices: list[dict], overdue: list[dict], escalated: list[dict]) -> None:
    total = len(invoices)
    overdue_count = len(overdue)
    escalated_count = len(escalated)
    pending = sum(1 for invoice in invoices if invoice.get("payment_status") == "PENDING")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Invoices", total)
    col2.metric("Overdue Invoices", overdue_count)
    col3.metric("Escalations", escalated_count)
    col4.metric("Pending", pending)


st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Dashboard", "Invoices", "Workflows", "AI Previews", "Audit Logs"])

st.sidebar.subheader("Upload (Placeholder)")
st.sidebar.file_uploader("Invoice CSV", type=["csv"], disabled=True)

st.sidebar.subheader("Backend Connectivity")
if st.sidebar.button("Test Health Endpoint"):
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        response.raise_for_status()
        st.sidebar.success(f"Backend OK: {response.json()}")
    except requests.RequestException as exc:
        st.sidebar.error(f"Backend not reachable: {exc}")

st.title("Finance Credit Follow-Up Email Agent")
st.markdown("**Status**: Deterministic workflow + hardened AI communication layer")

invoices, error = fetch_invoices()
overdue_invoices, overdue_error = fetch_workflow_overdue()
escalated_invoices, escalated_error = fetch_workflow_escalated()

if error:
    st.warning(f"Backend not reachable: {error}")

if overdue_error:
    st.warning(f"Workflow overdue fetch failed: {overdue_error}")

if escalated_error:
    st.warning(f"Workflow escalated fetch failed: {escalated_error}")

if page == "Dashboard":
    render_metrics(invoices, overdue_invoices, escalated_invoices)
    st.divider()

    st.subheader("Workflow Processing")
    if st.button("Process Overdue Invoices"):
        try:
            response = requests.post(f"{BACKEND_URL}/workflows/process-overdue", timeout=15)
            response.raise_for_status()
            st.success("Workflow processed successfully.")
            st.json(response.json())
        except requests.RequestException as exc:
            st.error(f"Workflow processing failed: {exc}")

    st.divider()
    st.subheader("Recent Invoices")
    if invoices:
        st.dataframe(invoices, use_container_width=True)
    else:
        st.info("No invoices available yet.")
elif page == "Invoices":
    st.subheader("Invoice List")
    if invoices:
        st.dataframe(invoices, use_container_width=True)
    else:
        st.info("No invoices available yet.")
elif page == "Workflows":
    st.subheader("Workflow Overview")
    render_metrics(invoices, overdue_invoices, escalated_invoices)
    st.divider()

    stage = st.selectbox(
        "Filter by Escalation Stage",
        [
            "STAGE_1",
            "STAGE_2",
            "STAGE_3",
            "STAGE_4",
            "LEGAL_ESCALATION",
        ],
    )
    stage_invoices, stage_error = fetch_workflow_stage(stage)
    if stage_error:
        st.warning(f"Stage fetch failed: {stage_error}")
    elif stage_invoices:
        st.dataframe(stage_invoices, use_container_width=True)
    else:
        st.info("No invoices for selected stage.")

    st.divider()
    st.subheader("Legal Escalations")
    legal_invoices, legal_error = fetch_workflow_stage("LEGAL_ESCALATION")
    if legal_error:
        st.warning(f"Legal escalation fetch failed: {legal_error}")
    elif legal_invoices:
        st.warning("Legal escalation requires immediate review.")
        st.dataframe(legal_invoices, use_container_width=True)
    else:
        st.info("No legal escalations.")
else:
    if page == "AI Previews":
        st.subheader("AI Email Preview Panel")
        overdue_ids = [inv.get("invoice_id") for inv in overdue_invoices if inv.get("invoice_id")]
        if not overdue_ids:
            st.info("No overdue invoices available for AI preview generation.")
        else:
            selected_invoice_id = st.selectbox("Select overdue invoice", overdue_ids)
            col_gen, col_fetch = st.columns(2)
            with col_gen:
                if st.button("Generate Preview for Selected Invoice"):
                    result, err = generate_ai_email(selected_invoice_id)
                    if err:
                        st.error(f"AI generation failed: {err}")
                    elif result:
                        st.success("AI preview generated successfully.")
                        if result.get("validation_passed"):
                            st.info(
                                f"Validation: passed | Latency: {result.get('generation_latency_ms')} ms | Prompt: {result.get('prompt_version')}"
                            )
                        else:
                            st.warning("Validation reported issues.")
                        if result.get("validation_issues"):
                            st.write("Validation issues:")
                            st.json(result.get("validation_issues"))
                        st.caption(
                            f"Tone consistent: {result.get('tone_consistent')} | Output complete: {result.get('output_complete')} | Stage prompt: {result.get('stage_prompt_name')}"
                        )
                        st.json(result)
            with col_fetch:
                if st.button("Fetch Latest Stored Preview"):
                    preview, err = fetch_ai_preview(selected_invoice_id)
                    if err:
                        st.error(f"Preview fetch failed: {err}")
                    elif preview:
                        st.subheader(preview.get("subject", "Generated Subject"))
                        st.caption(
                            f"Stage: {preview.get('escalation_stage')} | Tone: {preview.get('tone_used')} | Generated: {preview.get('generated_at')}"
                        )
                        st.text_area("Generated Email Body", preview.get("email_body", ""), height=260)

            st.divider()
            st.subheader("Batch Generation (Overdue)")
            batch_limit = st.slider("Batch size", min_value=1, max_value=50, value=10, step=1)
            if st.button("Generate Batch Previews"):
                batch_result, batch_err = generate_ai_batch(batch_limit)
                if batch_err:
                    st.error(f"Batch generation failed: {batch_err}")
                elif batch_result:
                    st.success(
                        f"Batch complete: generated={batch_result.get('generated_count')} failed={batch_result.get('failed_count')}"
                    )
                    failed_count = batch_result.get("failed_count", 0)
                    if failed_count:
                        st.warning("Some generations failed validation/provider checks.")
                    st.json(batch_result)
    else:
        st.subheader("Audit Logs")
        log_limit = st.slider("Logs to fetch", min_value=10, max_value=500, value=100, step=10)
        audit_logs, audit_error = fetch_audit_logs(log_limit)
        if audit_error:
            st.warning(f"Audit log fetch failed: {audit_error}")
        elif audit_logs:
            st.dataframe(audit_logs, use_container_width=True)
        else:
            st.info("No audit logs available.")

st.caption(f"Current view: {page}")
