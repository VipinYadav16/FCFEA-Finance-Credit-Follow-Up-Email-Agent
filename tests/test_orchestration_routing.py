from app.workflows.graph.graph_builder import _route_after_approval


def test_route_after_approval_to_delivery() -> None:
    state = {"approval_status": "APPROVED"}
    assert _route_after_approval(state) == "dry_run_delivery"


def test_route_after_approval_to_audit_complete() -> None:
    state = {"approval_status": "REJECTED"}
    assert _route_after_approval(state) == "audit_complete"


def test_route_after_approval_to_pause() -> None:
    state = {"approval_status": "PENDING"}
    assert _route_after_approval(state) == "pause"
