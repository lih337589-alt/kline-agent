import json
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.registry import AgentRunOutcome
from app.cache.redis import RedisCache
from app.core.config import settings
from app.core.limits import (
    LLM_MAX_CALLS_PER_ANALYSIS,
    LLM_MAX_INPUT_CHARS,
    LLM_MAX_RETRIES,
)
from app.llm.client import LLMClient
from app.models.report import Report
from app.models.stock import Stock
from app.repositories.agent_run import (
    create_agent_run,
)
from app.repositories.report import (
    create_report,
)
from app.repositories.stock import (
    get_stock_by_symbol,
)
from app.schemas.context import AnalysisContext
from app.schemas.features import (
    TechnicalFeatures,
    ValuationFeatures,
)
from app.services.context_builder import (
    ContextBuilder,
)
from app.services.feature_engineering import (
    build_technical_features,
    build_valuation_features,
)
from app.services.report_generator import (
    generate_report,
)
from app.workflows.analysis import (
    AnalysisWorkflow,
)


class StockNotFoundError(ValueError):
    pass


class AnalysisFailedError(RuntimeError):
    pass


@dataclass(frozen=True)
class AnalysisServiceResult:
    report: Report
    symbol: str
    trace_id: str


def run_analysis(
    db: Session,
    *,
    symbol: str,
    use_cache: bool = True,
) -> AnalysisServiceResult:
    normalized_symbol = symbol.strip().upper()

    stock = get_stock_by_symbol(
        db,
        normalized_symbol,
    )

    if stock is None:
        raise StockNotFoundError(f"Stock '{normalized_symbol}' not found")

    trace_id = uuid4().hex

    try:
        context = _build_context(
            db,
            stock,
            use_cache=use_cache,
        )

        technical = build_technical_features(
            db,
            stock,
        )

        valuation = build_valuation_features(
            db,
            stock,
        )

        llm_client = _build_llm_client()

        workflow = AnalysisWorkflow(llm_client)

        workflow_result = workflow.run(
            trace_id=trace_id,
            context=context,
            technical_features=technical,
            valuation_features=valuation,
        )

        input_summaries = _build_input_summaries(
            context,
            technical,
            valuation,
        )

        agent_run_ids = _persist_outcomes(
            db,
            stock=stock,
            trace_id=trace_id,
            outcomes=(workflow_result.outcomes),
            input_summaries=(input_summaries),
        )

        if (
            not workflow_result.analysis_succeeded
            or workflow_result.debate is None
            or workflow_result.cross_exam is None
            or workflow_result.judgment is None
        ):
            raise AnalysisFailedError(_build_failure_message(workflow_result))

        report_payload = generate_report(
            symbol=stock.symbol,
            company_name=stock.name,
            trace_id=trace_id,
            outcomes=(workflow_result.outcomes),
            debate=(workflow_result.debate),
            cross_exam=(workflow_result.cross_exam),
            judgment=(workflow_result.judgment),
            agent_run_ids=agent_run_ids,
        )

        report = create_report(
            db,
            stock_id=stock.id,
            trace_id=trace_id,
            title=(f"{stock.symbol} Multi-Agent Research Report"),
            report_json=(report_payload.model_dump_json()),
            status="completed",
            source=(settings.llm_provider),
        )

        db.commit()
        db.refresh(report)

        return AnalysisServiceResult(
            report=report,
            symbol=stock.symbol,
            trace_id=trace_id,
        )

    except Exception:
        db.rollback()
        raise


def _build_context(
    db: Session,
    stock: Stock,
    *,
    use_cache: bool,
) -> AnalysisContext:
    cache = RedisCache(settings.redis_url)

    builder = ContextBuilder(cache=cache)

    return builder.build(
        db,
        stock.symbol,
        use_cache=use_cache,
    )


def _build_llm_client() -> LLMClient:
    return LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout_seconds=(settings.llm_timeout_seconds),
        max_retries=LLM_MAX_RETRIES,
        max_calls=(LLM_MAX_CALLS_PER_ANALYSIS),
        max_input_chars=(LLM_MAX_INPUT_CHARS),
    )


def _build_context_summary(
    context: AnalysisContext,
) -> dict[str, object]:
    evidence_ids: list[str] = []

    if context.market.source_ref is not None:
        evidence_ids.append(context.market.source_ref.source_id)

    evidence_ids.extend(
        financial.source_ref.source_id for financial in context.financials
    )

    evidence_ids.extend(text.source_ref.source_id for text in context.texts)

    return {
        "symbol": context.symbol,
        "built_at": (context.built_at.isoformat()),
        "financial_count": len(context.financials),
        "text_count": len(context.texts),
        "evidence_ids": evidence_ids,
    }


def _build_input_summaries(
    context: AnalysisContext,
    technical: TechnicalFeatures,
    valuation: ValuationFeatures,
) -> dict[str, str]:
    context_summary = _build_context_summary(context)

    return {
        "fundamental": json.dumps(
            context_summary,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "valuation": (valuation.model_dump_json()),
        "technical": (technical.model_dump_json()),
        "sentiment": json.dumps(
            {
                "symbol": context.symbol,
                "text_count": len(context.texts),
                "evidence_ids": [item.source_ref.source_id for item in context.texts],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "risk": json.dumps(
            {
                "context": context_summary,
                "technical": (technical.model_dump(mode="json")),
                "valuation": (valuation.model_dump(mode="json")),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }


def _persist_outcomes(
    db: Session,
    *,
    stock: Stock,
    trace_id: str,
    outcomes: list[AgentRunOutcome],
    input_summaries: dict[str, str],
) -> list[int]:
    agent_run_ids: list[int] = []

    for outcome in outcomes:
        execution = outcome.execution

        if execution is not None:
            agent_run = create_agent_run(
                db,
                stock_id=stock.id,
                trace_id=trace_id,
                agent_type=outcome.agent_name,
                model_name=(execution.llm_call.model),
                status="success",
                input_summary=(input_summaries[outcome.agent_name]),
                output_json=(execution.result.model_dump_json()),
                error_message=None,
                duration_ms=(outcome.duration_ms),
                token_count=(execution.llm_call.total_tokens),
                source=(settings.llm_provider),
            )

        else:
            agent_run = create_agent_run(
                db,
                stock_id=stock.id,
                trace_id=trace_id,
                agent_type=outcome.agent_name,
                model_name=(settings.llm_model),
                status="error",
                input_summary=(input_summaries[outcome.agent_name]),
                output_json=None,
                error_message=(outcome.error_message),
                duration_ms=(outcome.duration_ms),
                token_count=None,
                source=(settings.llm_provider),
            )

        agent_run_ids.append(agent_run.id)

    return agent_run_ids


def _build_failure_message(
    workflow_result,
) -> str:
    errors: list[str] = []

    for outcome in workflow_result.outcomes:
        if outcome.error_message:
            errors.append(f"{outcome.agent_name}: {outcome.error_message}")

    if workflow_result.debate_error:
        errors.append(workflow_result.debate_error)

    if workflow_result.cross_error:
        errors.append(workflow_result.cross_error)

    if workflow_result.judge_error:
        errors.append(workflow_result.judge_error)

    if not errors:
        return "Analysis workflow failed"

    return "; ".join(errors)
