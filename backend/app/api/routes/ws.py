import asyncio
import logging

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.database.session import SessionLocal
from app.llm.client import LLMClient
from app.realtime.stream import (
    SimulatedMarketStream,
)
from app.repositories.risk_alert import (
    set_risk_alert_explanation,
)
from app.repositories.stock import (
    get_stock_by_symbol,
)
from app.risk.alerts import (
    persist_rule_hits,
)
from app.risk.explainer import (
    RiskExplainer,
    build_risk_event_package,
)
from app.risk.features import (
    RiskFeatureEngine,
)
from app.risk.rules import (
    RiskRuleEngine,
)
from app.schemas.risk import (
    FeatureSnapshot,
    RuleHit,
)
from app.services.context_builder import (
    ContextBuilder,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    tags=["realtime"],
)


_background_tasks: set[asyncio.Task[None]] = set()


def _get_stock_id(
    symbol: str,
) -> int | None:
    with SessionLocal() as db:
        stock = get_stock_by_symbol(
            db,
            symbol,
        )

        if stock is None:
            return None

        return stock.id


def _store_rule_hits(
    *,
    stock_id: int,
    snapshot: FeatureSnapshot,
    rule_hits: list[RuleHit],
) -> list[
    tuple[
        int,
        str,
    ]
]:
    with SessionLocal() as db:
        try:
            alerts = persist_rule_hits(
                db,
                stock_id=stock_id,
                snapshot=snapshot,
                rule_hits=rule_hits,
            )

            created = [
                (
                    alert.id,
                    alert.alert_type,
                )
                for alert in alerts
            ]

            db.commit()

            return created

        except Exception:
            db.rollback()
            raise


def _make_llm_client() -> LLMClient:
    return LLMClient(
        api_key=settings.llm_api_key,
        base_url=(settings.llm_base_url),
        model=settings.llm_model,
        timeout_seconds=(settings.llm_timeout_seconds),
    )


def _explain_and_store_alert(
    *,
    alert_id: int,
    symbol: str,
    snapshot: FeatureSnapshot,
    rule_hit: RuleHit,
) -> None:
    try:
        with SessionLocal() as db:
            context = ContextBuilder().build(
                db,
                symbol,
                use_cache=False,
            )

        event = build_risk_event_package(
            context=context,
            snapshot=snapshot,
            rule_hit=rule_hit,
        )

        explainer = RiskExplainer(_make_llm_client())

        explanation, call_info = explainer.explain(event)

        with SessionLocal() as db:
            alert = set_risk_alert_explanation(
                db,
                alert_id=alert_id,
                explanation_json=(explanation.model_dump_json()),
            )

            if alert is None:
                logger.warning(
                    "Risk alert %s no longer exists before explanation could be saved.",
                    alert_id,
                )

                return

            db.commit()

        logger.info(
            "Risk alert explanation saved: alert_id=%s symbol=%s model=%s tokens=%s",
            alert_id,
            symbol,
            call_info.model,
            call_info.total_tokens,
        )

    except Exception:
        logger.exception(
            "Risk alert explanation failed: alert_id=%s symbol=%s",
            alert_id,
            symbol,
        )


async def _run_risk_explanation(
    *,
    alert_id: int,
    symbol: str,
    snapshot: FeatureSnapshot,
    rule_hit: RuleHit,
) -> None:
    await asyncio.to_thread(
        _explain_and_store_alert,
        alert_id=alert_id,
        symbol=symbol,
        snapshot=snapshot,
        rule_hit=rule_hit,
    )


def _queue_risk_explanation(
    *,
    alert_id: int,
    symbol: str,
    snapshot: FeatureSnapshot,
    rule_hit: RuleHit,
) -> None:
    task = asyncio.create_task(
        _run_risk_explanation(
            alert_id=alert_id,
            symbol=symbol,
            snapshot=snapshot,
            rule_hit=rule_hit,
        )
    )

    _background_tasks.add(task)

    task.add_done_callback(_background_tasks.discard)


@router.websocket("/ws/market")
async def market_websocket(
    websocket: WebSocket,
) -> None:
    raw_symbol = websocket.query_params.get(
        "symbol",
        "AAPL",
    )

    symbol = raw_symbol.strip().upper()

    if not symbol:
        symbol = "AAPL"

    await websocket.accept()

    stream = SimulatedMarketStream(
        symbol=symbol,
    )

    feature_engine = RiskFeatureEngine(
        window_seconds=(settings.risk_feature_window_seconds),
    )

    rule_engine = RiskRuleEngine()

    stock_lookup_complete = False

    stock_id: int | None = None

    try:
        while True:
            tick = await stream.next_tick()

            snapshot = feature_engine.update(tick)

            rule_hits = rule_engine.evaluate(snapshot)

            created_alerts: list[
                tuple[
                    int,
                    str,
                ]
            ] = []

            if rule_hits:
                try:
                    if not stock_lookup_complete:
                        stock_id = _get_stock_id(symbol)

                        stock_lookup_complete = True

                    if stock_id is not None:
                        created_alerts = _store_rule_hits(
                            stock_id=stock_id,
                            snapshot=snapshot,
                            rule_hits=(rule_hits),
                        )

                except SQLAlchemyError:
                    logger.exception(
                        "Failed to persist risk alerts for %s.",
                        symbol,
                    )

            if created_alerts:
                hits_by_name = {hit.rule_name: hit for hit in rule_hits}

                for (
                    alert_id,
                    alert_type,
                ) in created_alerts:
                    rule_hit = hits_by_name.get(alert_type)

                    if rule_hit is None:
                        continue

                    _queue_risk_explanation(
                        alert_id=alert_id,
                        symbol=symbol,
                        snapshot=snapshot,
                        rule_hit=rule_hit,
                    )

            await websocket.send_json(
                tick.model_dump(
                    mode="json",
                )
            )

    except WebSocketDisconnect:
        return
