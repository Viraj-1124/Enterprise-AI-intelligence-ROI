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


def _mock_task_output(category: str, node_id: str, text: str, parent_outputs: object) -> str:
    context = parent_outputs if isinstance(parent_outputs, dict) else {}
    sentiment = _sentiment(text)
    issue = _issue(text)
    urgency = _urgency(text)
    risk = _risk(text)
    action = _recommended_action(text)

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
        return _mock_task_output(category, node_id, user_input, parent_outputs)
