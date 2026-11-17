from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

from app.agents.base import AgentExecution
from app.agents.fundamental import FundamentalAgent
from app.agents.risk import RiskAgent
from app.agents.sentiment import SentimentAgent
from app.agents.technical import TechnicalAgent
from app.agents.valuation import ValuationAgent
from app.llm.client import (
    LLMClient,
    LLMOutputError,
    LLMProviderError,
)
from app.schemas.context import AnalysisContext
from app.schemas.features import (
    TechnicalFeatures,
    ValuationFeatures,
)


@dataclass(frozen=True)
class AgentRunOutcome:
    agent_name: str
    execution: AgentExecution | None
    error_message: str | None
    duration_ms: int

    @property
    def succeeded(self) -> bool:
        return self.execution is not None


class AgentRegistry:
    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.fundamental = FundamentalAgent(llm_client)

        self.valuation = ValuationAgent(llm_client)

        self.technical = TechnicalAgent(llm_client)

        self.sentiment = SentimentAgent(llm_client)

        self.risk = RiskAgent(llm_client)

    def run_all(
        self,
        *,
        context: AnalysisContext,
        technical: TechnicalFeatures,
        valuation: ValuationFeatures,
    ) -> list[AgentRunOutcome]:
        outcomes: list[AgentRunOutcome] = []

        outcomes.append(
            self._run_one(
                "fundamental",
                lambda: self.fundamental.run(context),
            )
        )

        outcomes.append(
            self._run_one(
                "valuation",
                lambda: self.valuation.run(valuation),
            )
        )

        outcomes.append(
            self._run_one(
                "technical",
                lambda: self.technical.run(technical),
            )
        )

        outcomes.append(
            self._run_one(
                "sentiment",
                lambda: self.sentiment.run(context),
            )
        )

        outcomes.append(
            self._run_one(
                "risk",
                lambda: self.risk.run(
                    context,
                    technical,
                    valuation,
                ),
            )
        )

        return outcomes

    @staticmethod
    def _run_one(
        agent_name: str,
        runner: Callable[
            [],
            AgentExecution,
        ],
    ) -> AgentRunOutcome:
        started_at = perf_counter()

        try:
            execution = runner()

        except (
            ValueError,
            LLMProviderError,
            LLMOutputError,
        ) as exc:
            duration_ms = int((perf_counter() - started_at) * 1000)

            return AgentRunOutcome(
                agent_name=agent_name,
                execution=None,
                error_message=str(exc),
                duration_ms=duration_ms,
            )

        duration_ms = int((perf_counter() - started_at) * 1000)

        return AgentRunOutcome(
            agent_name=agent_name,
            execution=execution,
            error_message=None,
            duration_ms=duration_ms,
        )
