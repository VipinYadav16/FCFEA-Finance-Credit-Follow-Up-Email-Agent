import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Finance Credit Follow-Up Email Agent", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Dashboard", "Invoices", "Workflows", "Audit Logs"])

st.title("Finance Credit Follow-Up Email Agent")

st.markdown("**Status**: Prototype UI scaffold")

col1, col2, col3 = st.columns(3)
col1.metric("Overdue Invoices", "--")
col2.metric("Escalations", "--")
col3.metric("Pending Reviews", "--")

st.divider()

st.subheader("Backend Connectivity")

if st.button("Test Health Endpoint"):
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        response.raise_for_status()
        st.success(f"Backend OK: {response.json()}")
    except requests.RequestException as exc:
        st.error(f"Backend not reachable: {exc}")

st.caption(f"Current view: {page}")
