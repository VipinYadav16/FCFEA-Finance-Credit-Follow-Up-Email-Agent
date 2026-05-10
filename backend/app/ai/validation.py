import re
from dataclasses import dataclass
from decimal import Decimal

from app.models.schemas import AIEmailOutput, WorkflowInvoiceContext

FORBIDDEN_PATTERNS = [
    r"legal action has already started",
    r"final warning before lawsuit",
    r"penalty has been added",
    r"\blawsuit\b",
    r"\bcriminal proceedings\b",
    r"\bharass\b",
    r"\bblacklist\b",
    r"\bpay immediately or else\b",
]

UNSAFE_TONE_PATTERNS = [
    r"\bthreat\b",
    r"\bpunish\b",
    r"\bshame\b",
    r"\bembarrass\b",
    r"\bcoerce\b",
]


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: str = "error"


@dataclass
class ValidationResult:
    is_valid: bool
    issues: list[ValidationIssue]


def _find_patterns(text: str, patterns: list[str], code: str, message: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(ValidationIssue(code=code, message=message))
            break
    return issues


def validate_required_fields(output: AIEmailOutput) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not output.subject.strip():
        issues.append(ValidationIssue(code="required_subject", message="Subject is empty"))
    if not output.email_body.strip():
        issues.append(ValidationIssue(code="required_body", message="Email body is empty"))
    if not output.tone_used.strip():
        issues.append(ValidationIssue(code="required_tone", message="Tone value is empty"))
    return issues


def validate_formatting(output: AIEmailOutput) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if "\t" in output.email_body:
        issues.append(ValidationIssue(code="invalid_formatting_tabs", message="Tab characters are not allowed"))
    if len(output.subject.split()) < 2:
        issues.append(ValidationIssue(code="invalid_subject_format", message="Subject appears too short"))
    return issues


def validate_forbidden_language(output: AIEmailOutput) -> list[ValidationIssue]:
    merged = f"{output.subject}\n{output.email_body}"
    issues = _find_patterns(
        merged,
        FORBIDDEN_PATTERNS,
        code="forbidden_phrase",
        message="Forbidden legal/aggressive phrase detected",
    )
    issues.extend(
        _find_patterns(
            merged,
            UNSAFE_TONE_PATTERNS,
            code="unsafe_tone",
            message="Unsafe manipulative/aggressive language detected",
        )
    )
    return issues


def validate_hallucination(output: AIEmailOutput, context: WorkflowInvoiceContext) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    amount_token = f"{Decimal(context.amount_due):.2f}"
    due_date_token = context.due_date.isoformat()
    if context.invoice_id not in output.email_body:
        issues.append(ValidationIssue(code="invoice_id_mismatch", message="invoice_id missing from output body"))
    if amount_token not in output.email_body:
        issues.append(ValidationIssue(code="amount_mismatch", message="amount_due missing from output body"))
    if due_date_token not in output.email_body:
        issues.append(ValidationIssue(code="due_date_mismatch", message="due_date missing from output body"))
    if output.escalation_stage != context.escalation_stage:
        issues.append(ValidationIssue(code="stage_mismatch", message="Escalation stage mismatch"))
    return issues


def validate_ai_output(output: AIEmailOutput, context: WorkflowInvoiceContext) -> ValidationResult:
    issues: list[ValidationIssue] = []
    issues.extend(validate_required_fields(output))
    issues.extend(validate_formatting(output))
    issues.extend(validate_forbidden_language(output))
    issues.extend(validate_hallucination(output, context))
    return ValidationResult(is_valid=len(issues) == 0, issues=issues)
