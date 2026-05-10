from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.workflows.graph.nodes import (
    ai_generation_node,
    ai_validation_node,
    approval_wait_node,
    audit_complete_node,
    dry_run_delivery_node,
    fetch_invoice_node,
    preview_creation_node,
    process_workflow_node,
)
from app.workflows.graph.state import OrchestrationState


def _route_after_approval(state: OrchestrationState) -> str:
    approval_status = state.get("approval_status")
    if approval_status == "APPROVED":
        return "dry_run_delivery"
    if approval_status == "REJECTED":
        return "audit_complete"
    return "pause"


def build_workflow_graph(db: Session):
    graph = StateGraph(OrchestrationState)

    graph.add_node("fetch_invoice", fetch_invoice_node(db))
    graph.add_node("workflow_processing", process_workflow_node(db))
    graph.add_node("ai_generation", ai_generation_node(db))
    graph.add_node("ai_validation", ai_validation_node())
    graph.add_node("preview_creation", preview_creation_node(db))
    graph.add_node("approval_wait", approval_wait_node(db))
    graph.add_node("dry_run_delivery", dry_run_delivery_node(db))
    graph.add_node("audit_complete", audit_complete_node(db))

    graph.add_edge(START, "fetch_invoice")
    graph.add_edge("fetch_invoice", "workflow_processing")
    graph.add_edge("workflow_processing", "ai_generation")
    graph.add_edge("ai_generation", "ai_validation")
    graph.add_edge("ai_validation", "preview_creation")
    graph.add_edge("preview_creation", "approval_wait")
    graph.add_conditional_edges(
        "approval_wait",
        _route_after_approval,
        {
            "dry_run_delivery": "dry_run_delivery",
            "audit_complete": "audit_complete",
            "pause": END,
        },
    )
    graph.add_edge("dry_run_delivery", "audit_complete")
    graph.add_edge("audit_complete", END)

    return graph.compile()


def build_resume_graph(db: Session):
    graph = StateGraph(OrchestrationState)
    graph.add_node("approval_wait", approval_wait_node(db))
    graph.add_node("dry_run_delivery", dry_run_delivery_node(db))
    graph.add_node("audit_complete", audit_complete_node(db))

    graph.add_edge(START, "approval_wait")
    graph.add_conditional_edges(
        "approval_wait",
        _route_after_approval,
        {
            "dry_run_delivery": "dry_run_delivery",
            "audit_complete": "audit_complete",
            "pause": END,
        },
    )
    graph.add_edge("dry_run_delivery", "audit_complete")
    graph.add_edge("audit_complete", END)
    return graph.compile()
