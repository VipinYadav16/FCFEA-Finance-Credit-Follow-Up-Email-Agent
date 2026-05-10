# Presentation Notes

## Business Problem

Finance teams lose time and consistency in overdue follow-up communication. Manual reminders are hard to scale and hard to audit.

## Solution

This platform combines deterministic workflow control with constrained AI communication and governed delivery execution.

## Core Architecture

- Deterministic workflow layer for overdue detection and escalation.
- AI communication layer for safe, stage-aware email wording.
- Delivery governance layer for approval and dry-run execution.
- LangGraph orchestration layer for stateful coordination and traceability.

## AI Governance

- Externalized prompts by escalation stage.
- Structured output schema validation.
- Forbidden phrase and hallucination checks.
- Prompt-injection mitigation for customer-controlled fields.

## LangGraph Value

- Clear node sequencing over existing services.
- Approval pause/resume orchestration support.
- Node-level execution trace with timing and status.

## Security and Safety

- No autonomous sending.
- Human approval before any execution.
- Audit logs for generation, approval, dry-run, orchestration.
- API key through environment variables only.

## Business Value

- Faster follow-up preparation.
- Consistent communication quality.
- Improved compliance and auditability.
- Safer path to future SMTP and production orchestration.
