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
page = st.sidebar.selectbox("Go to", ["Dashboard", "Invoices", "Workflows", "Audit Logs"])

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
st.markdown("**Status**: Deterministic workflow engine")

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
