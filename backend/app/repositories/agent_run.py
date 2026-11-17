from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun


def create_agent_run(
    db: Session,
    *,
    stock_id: int,
    trace_id: str,
    agent_type: str,
    model_name: str | None,
    status: str,
    input_summary: str | None = None,
    output_json: str | None = None,
    error_message: str | None = None,
    duration_ms: int | None = None,
    token_count: int | None = None,
    source: str = "llm",
) -> AgentRun:
    agent_run = AgentRun(
        stock_id=stock_id,
        trace_id=trace_id,
        agent_type=agent_type,
        model_name=model_name,
        status=status,
        input_summary=input_summary,
        output_json=output_json,
        error_message=error_message,
        duration_ms=duration_ms,
        token_count=token_count,
        source=source,
    )

    db.add(agent_run)

    db.flush()

    return agent_run
