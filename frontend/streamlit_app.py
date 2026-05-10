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


def render_metrics(invoices: list[dict]) -> None:
    total = len(invoices)
    overdue = sum(1 for invoice in invoices if invoice.get("is_overdue"))
    escalated = sum(1 for invoice in invoices if invoice.get("payment_status") == "ESCALATED")
    pending = sum(1 for invoice in invoices if invoice.get("payment_status") == "PENDING")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Invoices", total)
    col2.metric("Overdue Invoices", overdue)
    col3.metric("Escalations", escalated)
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
st.markdown("**Status**: Invoice domain foundation")

invoices, error = fetch_invoices()
if error:
    st.warning(f"Backend not reachable: {error}")

if page == "Dashboard":
    render_metrics(invoices)
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
    st.subheader("Workflows")
    st.info("Workflow orchestration will appear here in a later phase.")
else:
    st.subheader("Audit Logs")
    st.info("Audit log viewer will appear here in a later phase.")

st.caption(f"Current view: {page}")
