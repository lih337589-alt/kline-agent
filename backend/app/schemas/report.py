from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import AgentResult
from app.schemas.debate import DebateResult
from app.schemas.review import (
    CrossExamResult,
    JudgeResult,
)


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    symbol: str = Field(
        min_length=1,
        max_length=32,
    )

    use_cache: bool = True


class AnalysisCreatedResponse(BaseModel):
    report_id: int
    trace_id: str
    symbol: str
    status: str


class ReportPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    symbol: str
    company_name: str
    trace_id: str

    executive_summary: str

    fundamental: AgentResult
    valuation: AgentResult
    technical: AgentResult
    sentiment: AgentResult
    risk: AgentResult

    debate: DebateResult
    cross_exam: CrossExamResult
    judgment: JudgeResult

    sources: list[str]

    agent_run_ids: list[int]


class ReportRead(BaseModel):
    id: int
    stock_id: int

    symbol: str
    trace_id: str
    title: str
    status: str
    source: str

    report: ReportPayload

    created_at: datetime
