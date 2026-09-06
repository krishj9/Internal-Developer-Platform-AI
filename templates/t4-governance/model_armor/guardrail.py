"""
Model Armor reference guardrail and inspection engine for IDP agent workloads.
"""

import re
from enum import StrEnum
from typing import Any


class InspectionPoint(StrEnum):
    PROMPT = "prompt"
    TOOL_INPUT = "tool_input"
    RETRIEVED_CONTENT = "retrieved_content"
    MODEL_OUTPUT = "model_output"


class PolicyAction(StrEnum):
    BLOCK = "block"
    REDACT = "redact"
    ALLOW_WITH_AUDIT = "allow_with_audit"


# Standard PII and Sensitive Patterns
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}-){3}\d{4}\b|\b\d{16}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

# Jailbreak & Injection heuristics
JAILBREAK_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+dan\s+mode", re.IGNORECASE),
    re.compile(r"system\s+override\s+code", re.IGNORECASE),
    re.compile(r"bypass\s+all\s+security\s+filters", re.IGNORECASE),
]


class ModelArmorGuardrail:
    """
    Evaluates prompts, tool inputs, retrieved chunks, and model outputs against safety policies.
    """

    def __init__(
        self,
        mode: PolicyAction = PolicyAction.BLOCK,
        pii_detection: bool = True,
        prompt_injection_filter: bool = True,
    ):
        self.mode = mode
        self.pii_detection = pii_detection
        self.prompt_injection_filter = prompt_injection_filter

    def inspect(
        self,
        text: str,
        point: InspectionPoint = InspectionPoint.PROMPT,
    ) -> dict[str, Any]:
        """
        Inspect text content at the given lifecycle point.
        """
        violations: list[str] = []
        sanitized_text = text

        # 1. Prompt Injection / Jailbreak check
        if self.prompt_injection_filter and point in (
            InspectionPoint.PROMPT,
            InspectionPoint.TOOL_INPUT,
        ):
            for pattern in JAILBREAK_PATTERNS:
                if pattern.search(text):
                    violations.append("prompt_injection_detected")
                    break

        # 2. PII Detection and Redaction
        if self.pii_detection:
            if SSN_PATTERN.search(sanitized_text):
                violations.append("ssn_detected")
                sanitized_text = SSN_PATTERN.sub("[REDACTED_SSN]", sanitized_text)

            if CREDIT_CARD_PATTERN.search(sanitized_text):
                violations.append("credit_card_detected")
                sanitized_text = CREDIT_CARD_PATTERN.sub("[REDACTED_CC]", sanitized_text)

            if EMAIL_PATTERN.search(sanitized_text):
                violations.append("email_detected")
                sanitized_text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized_text)

        # 3. Determine Outcome based on Mode
        if not violations:
            return {
                "passed": True,
                "action_taken": "allowed",
                "point": point.value,
                "original_text": text,
                "processed_text": text,
                "violations": [],
            }

        if self.mode == PolicyAction.BLOCK:
            return {
                "passed": False,
                "action_taken": "blocked",
                "point": point.value,
                "original_text": text,
                "processed_text": None,
                "violations": violations,
                "reason": f"Blocked by Model Armor policy at {point.value}: {violations}",
            }
        elif self.mode == PolicyAction.REDACT:
            return {
                "passed": True,
                "action_taken": "redacted",
                "point": point.value,
                "original_text": text,
                "processed_text": sanitized_text,
                "violations": violations,
            }
        else:  # ALLOW_WITH_AUDIT
            return {
                "passed": True,
                "action_taken": "allowed_with_audit",
                "point": point.value,
                "original_text": text,
                "processed_text": text,
                "violations": violations,
                "audit_note": f"Policy violation detected but permitted under audit: {violations}",
            }
