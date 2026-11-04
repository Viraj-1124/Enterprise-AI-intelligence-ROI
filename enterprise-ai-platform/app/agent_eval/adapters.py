"""Minimal adapter contracts and optional framework bridges."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass
class AgentStep:
    kind: str
    content: str = ""
    tool: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    agent: str | None = None


@dataclass
class AgentTranscript:
    output: str
    steps: list[AgentStep] = field(default_factory=list)
    context: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentAdapter(Protocol):
    name: str

    async def run(self, prompt: str, tools: list[dict[str, Any]], **kwargs: Any) -> AgentTranscript: ...


class CallableAdapter:
    """Wrap any async or sync callable returning an AgentTranscript or compatible dict."""

    def __init__(self, agent: Callable[..., Any], name: str = "callable") -> None:
        self.agent, self.name = agent, name

    async def run(self, prompt: str, tools: list[dict[str, Any]], **kwargs: Any) -> AgentTranscript:
        import inspect

        result = self.agent(prompt=prompt, tools=tools, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, AgentTranscript):
            return result
        if isinstance(result, dict):
            steps = [s if isinstance(s, AgentStep) else AgentStep(**s) for s in result.get("steps", [])]
            return AgentTranscript(**{**result, "steps": steps})
        raise TypeError("Agent callable must return AgentTranscript or a compatible dict")


class LangChainAdapter(CallableAdapter):
    """Bridge a LangChain Runnable; import LangChain only when a user installs it."""

    def __init__(self, runnable: Any, name: str = "langchain") -> None:
        async def invoke(prompt: str, tools: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
            value = runnable.invoke({"input": prompt, "tools": tools, **kwargs})
            output = value.get("output", value.get("answer", str(value))) if isinstance(value, dict) else str(value)
            return {"output": output, "steps": value.get("steps", []) if isinstance(value, dict) else []}

        super().__init__(invoke, name)


class CrewAIAdapter(CallableAdapter):
    """Bridge a CrewAI crew through its kickoff method."""

    def __init__(self, crew: Any, name: str = "crewai") -> None:
        async def invoke(prompt: str, tools: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
            result = crew.kickoff(inputs={"input": prompt, **kwargs})
            return {"output": str(result), "steps": [], "metadata": {"framework": "crewai"}}

        super().__init__(invoke, name)
