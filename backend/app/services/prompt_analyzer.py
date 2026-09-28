"""
Deterministic, rule-based prompt analysis (Section 19-20). No LLM call.
"""
import re

TECH_KEYWORDS = [
    "fastapi", "django", "flask", "react", "next.js", "nextjs", "vue", "angular",
    "python", "javascript", "typescript", "java", "golang", " go ", "rust", "sql",
    "postgres", "postgresql", "mysql", "sqlite", "mongodb", "sqlalchemy", "docker",
    "kubernetes", "node.js", "nodejs", "express", "spring", "graphql",
]
TEST_KEYWORDS = ["test", "tests", "testing", "unit test", "integration test", "pytest", "jest"]
EDGE_CASE_KEYWORDS = ["edge case", "error", "failure", "invalid", "exception", "validation"]
OUTPUT_KEYWORDS = ["return", "output", "response", "status code", "format", "schema"]
CONSTRAINT_KEYWORDS = ["must", "should", "constraint", "requirement", "limit", "performance"]


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(k in lowered for k in keywords)


def analyze_prompt(prompt: str) -> dict:
    text = prompt.strip()
    word_count = len(text.split())

    has_tech = _contains_any(text, TECH_KEYWORDS)
    has_tests = _contains_any(text, TEST_KEYWORDS)
    has_edge_cases = _contains_any(text, EDGE_CASE_KEYWORDS)
    has_output_spec = _contains_any(text, OUTPUT_KEYWORDS)
    has_constraints = _contains_any(text, CONSTRAINT_KEYWORDS)
    has_verbs = bool(re.search(r"\b(build|create|implement|write|add|fix|refactor|design)\b", text, re.I))

    missing = []
    if not has_tech:
        missing.append("technology/framework")
    if not has_output_spec:
        missing.append("expected output")
    if not has_constraints:
        missing.append("constraints")
    if not has_edge_cases:
        missing.append("edge cases")
    if not has_tests:
        missing.append("testing requirements")
    if word_count < 8:
        missing.append("context")

    # Scores 0-100, deterministic heuristics only.
    clarity = 80 if has_verbs else 40
    context = min(100, word_count * 4)
    specificity = 20 * sum([has_tech, has_output_spec, has_constraints, has_edge_cases, has_tests])
    output_requirements = 100 if has_output_spec else 20
    ambiguity = 100 - (30 if word_count < 8 else 0) - (20 if not has_tech else 0)
    ambiguity = max(0, min(100, ambiguity))
    completeness = round(
        (int(has_tech) + int(has_output_spec) + int(has_constraints) + int(has_edge_cases) + int(has_tests)) / 5 * 100
    )

    scores = {
        "clarity": clarity,
        "context": context,
        "specificity": specificity,
        "output_requirements": output_requirements,
        "ambiguity": ambiguity,
        "completeness": completeness,
    }

    suggestions = []
    if not has_tech:
        suggestions.append("Specify the technology/framework to use (e.g. FastAPI, React, PostgreSQL).")
    if not has_output_spec:
        suggestions.append("Describe the expected output or response format.")
    if not has_constraints:
        suggestions.append("State any constraints or non-functional requirements (performance, validation rules).")
    if not has_edge_cases:
        suggestions.append("Call out edge cases and error conditions the solution must handle.")
    if not has_tests:
        suggestions.append("Ask explicitly for unit/integration tests to be included.")
    if word_count < 8:
        suggestions.append("Add more context about the goal and who/what this is for.")
    if not suggestions:
        suggestions.append("This prompt already covers the key elements; consider adding a concrete example.")

    improved_prompt = _build_improved_prompt(text, has_tech, has_output_spec, has_constraints, has_edge_cases, has_tests)

    return {
        "scores": scores,
        "missing": missing,
        "suggestions": suggestions,
        "improved_prompt": improved_prompt,
    }


def _build_improved_prompt(original: str, has_tech, has_output_spec, has_constraints, has_edge_cases, has_tests) -> str:
    lines = [original.rstrip(".") + "."]
    if not has_tech:
        lines.append("Use [specify framework/language, e.g. FastAPI with PostgreSQL and SQLAlchemy].")
    if not has_output_spec:
        lines.append("Return [specify response format/status codes/schema].")
    if not has_constraints:
        lines.append("Constraints: [state performance, security, or business rules that apply].")
    if not has_edge_cases:
        lines.append("Handle edge cases such as invalid input, missing data, and failure conditions.")
    if not has_tests:
        lines.append("Include unit and integration tests covering success, validation failure, and error cases.")
    return "\n".join(lines)
