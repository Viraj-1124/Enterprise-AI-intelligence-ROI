"""
Provider connectors.

IMPORTANT: OpenAI, Anthropic, and Google do not expose a public API for a
given API key's own historical token usage / spend in a way that this
prototype can call generically (usage dashboards are account-console-only
and not part of the standard completions API). So these connectors report
is_available() = True only for the narrow thing they can legitimately do
(making a request and reading token counts FROM THAT REQUEST'S OWN
RESPONSE), and are honest that historical/organization-wide usage requires
a source this prototype does not have. GitHub's API does legitimately
expose commit/PR activity for a configured token, so that connector is
more capable.
"""
from datetime import datetime, timezone

from app.config import get_settings
from app.connectors.base import BaseConnector, ConnectorStatus, NormalizedEvent

settings = get_settings()


class OpenAIConnector(BaseConnector):
    name = "openai"

    def is_available(self) -> ConnectorStatus:
        if not settings.OPENAI_API_KEY:
            return ConnectorStatus(False, "No supported external telemetry source configured")
        return ConnectorStatus(
            True,
            "API key configured: can attribute cost only for requests made "
            "through this platform's own calls, not historical org-wide usage.",
        )

    def collect(self) -> list[dict]:
        if not self.is_available().available:
            return []
        # A real implementation would record token usage returned by calls
        # THIS platform makes on the user's behalf. There is no bulk
        # historical-usage endpoint to backfill from, so we return nothing
        # here rather than inventing records.
        return []

    def normalize(self, data: dict) -> NormalizedEvent:
        return NormalizedEvent(
            employee_id=data.get("employee_id"),
            task_id=data.get("task_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_type="ai_request",
            source="connector",
            tool="openai",
            metadata=data,
        )


class ClaudeConnector(BaseConnector):
    name = "anthropic"

    def is_available(self) -> ConnectorStatus:
        if not settings.ANTHROPIC_API_KEY:
            return ConnectorStatus(False, "No supported external telemetry source configured")
        return ConnectorStatus(
            True,
            "API key configured: can attribute cost only for requests made "
            "through this platform's own calls, not historical org-wide usage.",
        )

    def collect(self) -> list[dict]:
        if not self.is_available().available:
            return []
        return []

    def normalize(self, data: dict) -> NormalizedEvent:
        return NormalizedEvent(
            employee_id=data.get("employee_id"),
            task_id=data.get("task_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_type="ai_request",
            source="connector",
            tool="claude",
            metadata=data,
        )


class GeminiConnector(BaseConnector):
    name = "google"

    def is_available(self) -> ConnectorStatus:
        if not settings.GOOGLE_API_KEY:
            return ConnectorStatus(False, "No supported external telemetry source configured")
        return ConnectorStatus(
            True,
            "API key configured: can attribute cost only for requests made "
            "through this platform's own calls, not historical org-wide usage.",
        )

    def collect(self) -> list[dict]:
        if not self.is_available().available:
            return []
        return []

    def normalize(self, data: dict) -> NormalizedEvent:
        return NormalizedEvent(
            employee_id=data.get("employee_id"),
            task_id=data.get("task_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_type="ai_request",
            source="connector",
            tool="gemini",
            metadata=data,
        )


class GitHubConnector(BaseConnector):
    """
    The one connector that can legitimately backfill real historical
    activity: GitHub's REST API exposes commits/PRs for a configured token.
    """

    name = "github"

    def is_available(self) -> ConnectorStatus:
        if not settings.GITHUB_TOKEN:
            return ConnectorStatus(False, "No supported external telemetry source configured")
        return ConnectorStatus(True, "GitHub token configured")

    def collect(self) -> list[dict]:
        status = self.is_available()
        if not status.available:
            return []
        # A real implementation calls api.github.com/repos/{owner}/{repo}/commits
        # (or /events) with the configured token. Left as an integration
        # point: this prototype does not know which repo(s) to poll without
        # additional configuration, so it returns no records rather than
        # guessing a repository.
        return []

    def normalize(self, data: dict) -> NormalizedEvent:
        return NormalizedEvent(
            employee_id=data.get("employee_id"),
            task_id=data.get("task_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_type="commit",
            source="connector",
            tool="github",
            metadata=data,
        )


class JiraConnector(BaseConnector):
    name = "jira"

    def is_available(self) -> ConnectorStatus:
        return ConnectorStatus(False, "No supported external telemetry source configured")

    def collect(self) -> list[dict]:
        return []

    def normalize(self, data: dict) -> NormalizedEvent:
        return NormalizedEvent(
            employee_id=data.get("employee_id"),
            task_id=data.get("task_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_type="task_started",
            source="connector",
            tool="jira",
            metadata=data,
        )


class AntigravityConnector(BaseConnector):
    """
    Antigravity is treated strictly as an external, unmodified work tool.
    This connector never attempts to reach into Antigravity's internals,
    private prompts, tokens, or costs. It always reports unavailable for
    AI-specific telemetry; externally observable work evidence (sessions,
    git activity, tests) is collected separately by the `collector`, not
    through this connector.
    """

    name = "antigravity"

    def is_available(self) -> ConnectorStatus:
        return ConnectorStatus(
            False,
            "Antigravity exposes no legitimate external API for AI token/cost/prompt "
            "telemetry; this platform does not access Antigravity internals.",
        )

    def collect(self) -> list[dict]:
        return []

    def normalize(self, data: dict) -> NormalizedEvent:
        return NormalizedEvent(
            employee_id=data.get("employee_id"),
            task_id=data.get("task_id"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            event_type="ai_request",
            source="unavailable",
            tool="antigravity",
            metadata=data,
        )


ALL_CONNECTORS: dict[str, type[BaseConnector]] = {
    "openai": OpenAIConnector,
    "anthropic": ClaudeConnector,
    "google": GeminiConnector,
    "github": GitHubConnector,
    "jira": JiraConnector,
    "antigravity": AntigravityConnector,
}
