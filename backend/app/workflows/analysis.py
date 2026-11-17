from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.agents.base import AgentExecution
from app.agents.fundamental import FundamentalAgent
from app.agents.registry import AgentRunOutcome
from app.agents.risk import RiskAgent
from app.agents.sentiment import SentimentAgent
from app.agents.technical import TechnicalAgent
from app.agents.valuation import ValuationAgent
from app.llm.client import LLMClient, LLMOutputError, LLMProviderError
from app.agents.bear import BearAgent
from app.agents.bull import BullAgent
from app.schemas.debate import BullCase, DebateResult


class AnalysisWorkflowState(TypedDict):
    trace_id: str
    context: Any
    technical_features: Any
    valuation_features: Any
    outcomes: list[AgentRunOutcome]


@dataclass(frozen=True)
class AnalysisWorkflowResult:
    trace_id: str
    outcomes: list[AgentRunOutcome]

    @property
    def success_count(self) -> int:
        return sum(outcome.succeeded for outcome in self.outcomes)

    @property
    def error_count(self) -> int:
        return len(self.outcomes) - self.success_count


class AnalysisWorkflow:
    def __init__(self, llm_client: LLMClient) -> None:
        self._fundamental = FundamentalAgent(llm_client)
        self._valuation = ValuationAgent(llm_client)
        self._technical = TechnicalAgent(llm_client)
        self._sentiment = SentimentAgent(llm_client)
        self._risk = RiskAgent(llm_client)

        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        builder = StateGraph(AnalysisWorkflowState)

        builder.add_node("fundamental", self._fundamental_node)
        builder.add_node("valuation", self._valuation_node)
        builder.add_node("technical", self._technical_node)
        builder.add_node("sentiment", self._sentiment_node)
        builder.add_node("risk", self._risk_node)

        builder.add_edge(START, "fundamental")
        builder.add_edge("fundamental", "valuation")
        builder.add_edge("valuation", "technical")
        builder.add_edge("technical", "sentiment")
        builder.add_edge("sentiment", "risk")
        builder.add_edge("risk", END)

        return builder.compile(name="kline-analysis")

    def run(
        self,
        *,
        context: Any,
        technical_features: Any,
        valuation_features: Any,
        trace_id: str | None = None,
    ) -> AnalysisWorkflowResult:
        resolved_trace_id = trace_id or uuid4().hex

        final_state = self.graph.invoke(
            {
                "trace_id": resolved_trace_id,
                "context": context,
                "technical_features": technical_features,
                "valuation_features": valuation_features,
                "outcomes": [],
            }
        )

        return AnalysisWorkflowResult(
            trace_id=final_state["trace_id"],
            outcomes=final_state["outcomes"],
        )

    def _fundamental_node(
        self,
        state: AnalysisWorkflowState,
    ) -> dict[str, Any]:
        outcome = self._execute(
            "fundamental",
            lambda: self._fundamental.run(state["context"]),
        )
        return {"outcomes": [*state["outcomes"], outcome]}

    def _valuation_node(
        self,
        state: AnalysisWorkflowState,
    ) -> dict[str, Any]:
        outcome = self._execute(
            "valuation",
            lambda: self._valuation.run(state["valuation_features"]),
        )
        return {"outcomes": [*state["outcomes"], outcome]}

    def _technical_node(
        self,
        state: AnalysisWorkflowState,
    ) -> dict[str, Any]:
        outcome = self._execute(
            "technical",
            lambda: self._technical.run(state["technical_features"]),
        )
        return {"outcomes": [*state["outcomes"], outcome]}

    def _sentiment_node(
        self,
        state: AnalysisWorkflowState,
    ) -> dict[str, Any]:
        outcome = self._execute(
            "sentiment",
            lambda: self._sentiment.run(state["context"]),
        )
        return {"outcomes": [*state["outcomes"], outcome]}

    def _risk_node(
        self,
        state: AnalysisWorkflowState,
    ) -> dict[str, Any]:
        outcome = self._execute(
            "risk",
            lambda: self._risk.run(
                state["context"],
                state["technical_features"],
                state["valuation_features"],
            ),
        )
        return {"outcomes": [*state["outcomes"], outcome]}

    @staticmethod
    def _execute(
        agent_name: str,
        action: Callable[[], AgentExecution],
    ) -> AgentRunOutcome:
        started_at = perf_counter()

        try:
            execution = action()
        except (ValueError, LLMProviderError, LLMOutputError) as exc:
            duration_ms = int((perf_counter() - started_at) * 1000)

            return AgentRunOutcome(
                agent_name=agent_name,
                execution=None,
                error_message=f"{type(exc).__name__}: {exc}",
                duration_ms=duration_ms,
            )

        duration_ms = int((perf_counter() - started_at) * 1000)

        return AgentRunOutcome(
            agent_name=agent_name,
            execution=execution,
            error_message=None,
            duration_ms=duration_ms,
        )
