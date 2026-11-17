from dataclasses import dataclass

from app.llm.client import LLMCallInfo
from app.schemas.agent import AgentResult


@dataclass(frozen=True)
class AgentExecution:
    agent_name: str
    result: AgentResult
    llm_call: LLMCallInfo


class EvidenceValidationError(ValueError):
    pass
