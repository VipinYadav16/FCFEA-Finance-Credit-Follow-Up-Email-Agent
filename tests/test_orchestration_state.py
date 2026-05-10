from app.workflows.graph.state import OrchestrationState


def test_orchestration_state_shape_minimal() -> None:
    state: OrchestrationState = {
        "invoice_id": "INV-1",
        "workflow_status": "NOT_STARTED",
        "approval_status": "UNKNOWN",
        "validation_status": "UNKNOWN",
        "execution_trace": [],
        "should_send": False,
        "needs_approval": False,
    }
    assert state["invoice_id"] == "INV-1"
    assert state["workflow_status"] == "NOT_STARTED"
