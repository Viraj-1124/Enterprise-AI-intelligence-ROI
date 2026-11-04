import asyncio
import hashlib
import os
import random
import re
import threading

from app.core.enums import PrecisionTier
from app.core.schemas import ModelSpec

_flaky_seen: set[tuple[str, str]] = set()
_flaky_lock = threading.Lock()


def reset_flaky_state() -> None:
    with _flaky_lock:
        _flaky_seen.clear()


def _matches(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def _sentiment(text: str) -> str:
    positive = ("great", "good", "excellent", "helpful", "easy", "clear", "satisfied", "resolved", "friendly", "quick")
    negative = ("bad", "terrible", "awful", "late", "delayed", "missing", "never arrived", "difficult", "poor", "frustrated", "broken", "failed", "slow", "unhelpful")
    has_positive = _matches(text, positive)
    has_negative = _matches(text, negative)
    if has_positive and has_negative:
        return "Mixed — the request contains both positive and negative feedback."
    if has_positive:
        return "Positive — the request describes a favorable experience."
    if has_negative:
        return "Negative — the request describes a problem or dissatisfaction."
    return "Neutral — no clear positive or negative signal was found."


def _issue(text: str) -> str:
    if _matches(text, ("delivery", "package", "shipment", "tracking", "arrive", "shipping")):
        if _matches(text, ("late", "delay", "not arrived", "never arrived", "stalled", "missing")):
            return "Delivery delay or missing shipment update"
        return "Delivery or shipment question"
    if _matches(text, ("charged", "billing", "invoice", "payment", "refund", "subscription")):
        return "Billing or payment question"
    if _matches(text, ("login", "sign in", "password", "locked out", "account access")):
        return "Account access problem"
    if _matches(text, ("bug", "broken", "crash", "not working", "error")):
        return "Product issue or technical error"
    if _matches(text, ("checkout", "cart", "purchase")):
        return "Checkout or purchasing experience"
    return "No specific issue identified from the request"


def _urgency(text: str) -> str:
    if _matches(text, ("urgent", "immediately", "critical", "right away", "as soon as possible", "today")):
        return "High — the request signals immediate attention is needed."
    if _matches(text, ("soon", "follow up", "still waiting", "has not", "haven't", "cannot", "can't")):
        return "Medium — follow up is appropriate, but no immediate deadline was stated."
    return "Low — no time-sensitive language was found."


def _risk(text: str) -> str:
    if _matches(text, ("injury", "unsafe", "security breach", "account compromised", "fraud", "threat", "medical emergency")):
        return "High — potential safety, security, or fraud concern; escalate for human review."
    if _matches(text, ("personal data", "password", "social security", "credit card", "charged", "payment", "refund", "billing", "private information")):
        return "Moderate — financial or sensitive-data handling may require a policy check."
    if _matches(text, ("late", "delay", "missing", "not arrived", "never arrived", "tracking")):
        return "Moderate — unresolved service issue may affect customer trust; verify the status."
    return "Low — no explicit safety, security, financial, or privacy concern was detected."


def _recommended_action(text: str) -> str:
    if _matches(text, ("delivery", "package", "shipment", "tracking", "shipping", "arrive")):
        return "Check the latest carrier scan and delivery estimate, then send the customer a specific update."
    if _matches(text, ("charged twice", "duplicate charge", "refund")):
        return "Verify the transaction history and refund eligibility before taking any billing action."
    if _matches(text, ("charged", "billing", "invoice", "payment", "subscription")):
        return "Review the invoice and transaction record, then explain the next billing step."
    if _matches(text, ("login", "sign in", "password", "locked out", "account access")):
        return "Confirm account ownership and guide the customer through the approved recovery flow."
    if _matches(text, ("bug", "broken", "crash", "not working", "error")):
        return "Collect the affected feature and reproduction steps, then route the issue to technical support."
    if _matches(text, ("checkout", "cart", "purchase")):
        return "Reproduce the checkout issue and confirm whether the order was submitted successfully."
    return "Ask one focused follow-up question to confirm the issue, then route it to the responsible team."


def _extract_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else "No email address was provided."


def _support_queue(text: str) -> tuple[str, str]:
    lowered = text.lower()
    if _matches(lowered, ("vpn", "sign in", "login", "password", "locked out")):
        return "Account Access", "sign-in, password, or VPN access issue"
    if _matches(lowered, ("api", "crash", "bug", "error", "keeps failing", "not working")):
        return "Technical Support", "product or service error"
    if _matches(lowered, ("invoice", "billing", "subscription", "payment", "charged")):
        return "Billing", "invoice or payment question"
    return "General Support", "no specialist queue keyword matched"


def _redact_contact_details(text: str) -> tuple[str, list[str]]:
    redacted = text
    removed: list[str] = []
    redacted, count = re.subn(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED EMAIL]", redacted)
    if count:
        removed.append(f"{count} email address(es)")
    redacted, count = re.subn(
        r"(?i)\bcontact\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",
        "Contact [REDACTED NAME]",
        redacted,
    )
    if count:
        removed.append(f"{count} name(s)")
    redacted, count = re.subn(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)", "[REDACTED PHONE]", redacted)
    if count:
        removed.append(f"{count} phone number(s)")
    return redacted, removed


def _sentence_with_signal(text: str, words: tuple[str, ...]) -> str:
    clauses = re.split(r"(?<=[.!?])\s+|,\s+(?:and\s+)?|;\s*|\n+", text)
    return next((clause.strip(" .,:;") for clause in clauses if _matches(clause, words)), "")


def _mock_task_output(
    category: str,
    node_id: str,
    text: str,
    parent_outputs: object,
    task: str = "",
) -> str:
    context = parent_outputs if isinstance(parent_outputs, dict) else {}
    evidence = "\n".join([text, *(str(value) for value in context.values())])
    sentiment = _sentiment(evidence)
    issue = _issue(evidence)
    urgency = _urgency(evidence)
    risk = _risk(evidence)
    action = _recommended_action(evidence)
    task_text = task.lower()

    if node_id == "slm-ticket-router":
        queue, reason = _support_queue(text)
        return f"Assigned queue: {queue}\nReason: {reason}\nNext step: acknowledge the ticket and follow the queue's standard workflow."
    if node_id == "edge-redaction":
        redacted, removed = _redact_contact_details(text)
        removed_summary = ", ".join(removed) if removed else "No direct contact details detected"
        return f"Redacted note: {redacted}\nRemoved: {removed_summary}"
    if node_id == "precision-summary":
        report = re.split(r"(?i)\b(?:brief|report):\s*", text, maxsplit=1)[-1]
        result = _sentence_with_signal(report, ("improved", "increased", "reduced", "completed", "%"))
        limitation = _sentence_with_signal(report, ("failed", "failure", "issue", "limitation", "risk"))
        decision = _sentence_with_signal(report, ("recommend", "rollout", "fix", "before"))
        return (
            f"Measured result: {result or 'No measurable result stated.'}\n"
            f"Limitation: {limitation or 'No explicit limitation stated.'}\n"
            f"Recommendation: {decision or 'Review the findings before making a rollout decision.'}"
        )
    if node_id == "market-research-agent":
        duration = re.search(r"\b(\d+)\s*[- ]?months?\b", text, re.IGNORECASE)
        bookings = re.search(r"\b(\d[\d,]*)\s+(?:expected\s+)?monthly bookings\b|monthly bookings[^\d]{0,12}(\d[\d,]*)", text, re.IGNORECASE)
        booking_count = (bookings.group(1) or bookings.group(2)) if bookings else None
        milestones = "pilot launch and monthly adoption review" if duration or bookings else "confirm target users and adoption milestones"
        return (
            f"Pilot duration: {duration.group(1) + ' months' if duration else 'not specified'}\n"
            f"Expected demand: {booking_count + ' bookings/month' if booking_count else 'not specified'}\n"
            f"Milestone: {milestones}"
        )
    if node_id == "budget-agent":
        amount = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", text)
        duration = re.search(r"\b(\d+)\s*[- ]?months?\b", text, re.IGNORECASE)
        if amount and duration:
            total = float(amount.group(1).replace(",", ""))
            monthly = total / max(1, int(duration.group(1)))
            return f"Pilot budget: ${total:,.2f} total over {duration.group(1)} months (${monthly:,.2f}/month)."
        return "Budget estimate unavailable: include a total budget and pilot duration."
    if node_id == "launch-risk-agent":
        if _matches(text, ("bookings", "adoption", "pilot")):
            return "Risk: actual adoption may be lower than forecast. Mitigation: review bookings monthly and gate further spend on pilot results."
        return f"Risk: {risk} Mitigation: validate assumptions during the pilot."
    if node_id == "launch-synthesis-agent":
        findings = "\n".join(f"• {value}" for value in context.values())
        return f"Launch assessment\n{findings}\nDecision: run the pilot with monthly adoption and budget checkpoints."

    if node_id == "incident-planner-agent":
        return "Response plan: 1) verify service health and deployment version; 2) diagnose the authentication errors; 3) contain impact or roll back if confirmed; 4) validate recovery and publish an update."
    if node_id in {"incident-diagnosis-agent", "incident-diagnostics-agent"}:
        service = "authentication API" if _matches(text, ("authentication", "auth", "sign in", "login")) else "affected service"
        symptom = "HTTP 500 errors and users unable to sign in" if _matches(text, ("500", "sign in", "login")) else "reported service disruption"
        trigger = "recent deployment" if _matches(text, ("deployment", "release", "deploy")) else "trigger not yet confirmed"
        return f"Affected service: {service}\nObserved impact: {symptom}\nLikely trigger: {trigger}\nFirst check: compare errors with the latest release."
    if node_id in {"incident-mitigation-agent", "incident-mitigation"}:
        if _matches(evidence, ("500", "outage", "cannot sign in", "can't sign in", "deployment")):
            return "Containment: pause further rollout and assess rollback to the last healthy release. Recovery: validate authentication with a canary before restoring full traffic."
        return f"Containment: assign an incident owner and limit impact. Recovery: {action}"
    if node_id in {"incident-risk-agent", "incident-impact-agent"}:
        impact = "High — active sign-in failures affect customer access." if _matches(evidence, ("many users", "all users", "cannot sign in", "can't sign in", "500")) else f"{urgency} {risk}"
        return f"Incident impact: {impact}\nEscalation: notify the on-call service owner."
    if node_id in {"incident-communications-agent", "incident-update-agent"}:
        return "Customer update: We are investigating a sign-in issue affecting the authentication service. We will share another update after validating recovery."
    if node_id in {"incident-coordinator-agent", "incident-coordinator"}:
        work = "\n".join(f"• {value}" for value in context.values())
        return f"Prioritized incident response\n{work}\nOwner: on-call incident lead. Next checkpoint: confirm service health after mitigation."
    if node_id == "incident-analysis-agent":
        return f"Assessment: {issue}. {urgency} {risk} Recommended action: {action}"

    if node_id == "main" and category == "classification" and _matches(task_text, ("severity", "incident")):
        if _matches(text, ("critical", "outage", "many users", "500 errors", "cannot sign in")):
            return "Severity: HIGH — active service disruption with customer impact. Escalate to the on-call team."
        if _matches(text, ("some users", "intermittent", "degraded")):
            return "Severity: MEDIUM — partial or degraded service. Monitor impact and assign an owner."
        return "Severity: LOW — no broad outage signal detected. Continue standard triage."

    if node_id == "sentiment-slm":
        return sentiment
    if node_id == "customer-research":
        email = _extract_email(text)
        detail = "Email found: " + email if not email.startswith("No email") else "No contact email was included."
        return f"Main issue: {issue}.\nCustomer tone: {sentiment}\nUseful context: {detail}"
    if node_id == "risk-review":
        return f"Risk: {risk}\nUrgency: {urgency}"
    if node_id == "quality-review":
        return (
            f"Assessment: {issue}. {urgency} {risk}\n"
            f"Recommended follow-up: {action}"
        )
    if node_id == "orchestrator-synthesis":
        research = str(context.get("customer-research", f"Main issue: {issue}."))
        sentiment_result = str(context.get("sentiment-slm", sentiment))
        risk_result = str(context.get("risk-review", f"Risk: {risk} Urgency: {urgency}"))
        return (
            f"Case summary: {issue}.\n"
            f"Customer sentiment: {sentiment_result}\n"
            f"Risk and urgency: {risk_result}\n"
            f"Recommended next step: {action}"
        )
    if category == "classification":
        return sentiment
    if category == "extraction":
        return _extract_email(text)
    if category == "reasoning":
        return f"Issue: {issue}. Urgency: {urgency} Risk: {risk} Recommended action: {action}"
    if context:
        return (
            f"Summary: {issue}. Customer sentiment: {sentiment}\n"
            f"Risk: {risk}\nRecommended next step: {action}"
        )
    return f"Recommended next step: {action}"


class MockAdapter:
    provider = "mock"

    def __init__(
        self,
        spec: ModelSpec,
        min_latency_ms: int = 0,
        max_latency_ms: int = 0,
        failure_rate: float = 0.0,
    ) -> None:
        self.spec = spec
        self.min_latency_ms = min_latency_ms
        self.max_latency_ms = max_latency_ms
        self.failure_rate = failure_rate

    async def health(self) -> bool:
        return True

    async def generate(self, prompt: str, precision: PrecisionTier, **kwargs: object) -> str:
        mode = os.getenv("MOCK_MODE", "stable").lower()
        if mode == "always_fail":
            raise RuntimeError("simulated mock failure (MOCK_MODE=always_fail)")
        if mode == "flaky_first":
            key = (self.spec.id, hashlib.sha256(prompt.encode()).hexdigest())
            limited_model = os.getenv("MOCK_FAIL_FIRST_MODEL")
            with _flaky_lock:
                first = (
                    limited_model is None or limited_model == self.spec.id
                ) and key not in _flaky_seen
                _flaky_seen.add(key)
            if first:
                raise RuntimeError("simulated first-call failure (MOCK_MODE=flaky_first)")
        seed = int(hashlib.sha256((self.spec.id + prompt).encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        if self.max_latency_ms:
            await asyncio.sleep(rng.randint(self.min_latency_ms, self.max_latency_ms) / 1000)
        if rng.random() < self.failure_rate:
            raise RuntimeError("simulated provider failure")
        category = str(kwargs.get("category", "generation"))
        user_input = str(kwargs.get("user_input", prompt))
        node_id = str(kwargs.get("node_id", ""))
        parent_outputs = kwargs.get("parent_outputs", {})
        task = str(kwargs.get("task", ""))
        return _mock_task_output(category, node_id, user_input, parent_outputs, task)
