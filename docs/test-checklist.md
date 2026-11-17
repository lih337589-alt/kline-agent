# K线之上 MVP Test Checklist

Day 26 regression and smoke-test checklist.

The purpose of this checklist is to verify that the MVP's
critical paths remain reproducible before containerization
and final demonstration work.

## Backend API

- [x] Health endpoint is covered.
- [x] Stock lookup API is covered.
- [x] Analysis creation API is exercised by the E2E smoke test.
- [x] Persisted report retrieval API is covered.
- [x] Risk alerts API is covered.
- [x] Risk alert explanation serialization is covered.

## Database and repositories

- [x] Stock data can be created and queried.
- [x] Price data can be persisted and used by feature engineering.
- [x] Financial data can be consumed by analysis features.
- [x] Agent runs are persisted.
- [x] Reports are persisted and can be read again.
- [x] Risk alerts are persisted.
- [x] Risk explanations are persisted.

## Deterministic feature engines

- [x] Technical return calculations are tested.
- [x] Moving-average calculations are tested.
- [x] Volatility calculations are tested.
- [x] Valuation feature calculations are tested.
- [x] Realtime risk feature calculations are tested.
- [x] Risk rule thresholds are tested.
- [x] Risk alert cooldown/de-duplication is tested.

## Professional Agent regression

- [x] Fundamental Agent uses the shared AgentResult contract.
- [x] Valuation Agent uses the shared AgentResult contract.
- [x] Technical Agent uses the shared AgentResult contract.
- [x] Sentiment Agent uses the shared AgentResult contract.
- [x] Risk Agent uses the shared AgentResult contract.
- [x] Invalid evidence IDs are rejected where required.
- [x] Agent tests use fake LLM responses rather than live provider calls.

## Multi-Agent workflow

- [x] Professional Agents run in the expected workflow.
- [x] Bull review is covered.
- [x] Bear rebuttal is covered.
- [x] Cross examination is covered.
- [x] Judge review is covered.
- [x] Professional-Agent failure isolation is covered.
- [x] Workflow output can be converted into a structured report.

## Report pipeline

- [x] ReportGenerator requires all professional Agent outputs.
- [x] Executive summary comes from the Judge result.
- [x] Evidence/source IDs are collected into the report.
- [x] Report JSON is permanently persisted.
- [x] GET /api/reports/{report_id} reconstructs the report from storage.

## End-to-end smoke test

- [x] A temporary stock fixture is created in PostgreSQL.
- [x] Fixture market data is available to ContextBuilder.
- [x] Fixture financial data is available to ContextBuilder.
- [x] POST /api/analyses runs through the real application pipeline.
- [x] The LLM provider boundary is replaced with deterministic fake responses.
- [x] No real LLM provider request is required.
- [x] Five professional agent_runs are persisted.
- [x] A completed report is persisted.
- [x] GET /api/reports/{report_id} reads the persisted report.
- [x] Test fixture data is cleaned up after the test.

## Realtime risk

- [x] Simulated market WebSocket is covered.
- [x] Risk features consume realtime ticks.
- [x] Rule hits create risk alerts.
- [x] Cooldown suppresses duplicate alerts.
- [x] New alerts can receive an AI explanation.
- [x] Deterministic alerts survive explanation failure.
- [x] Alerts can be read by the frontend API.

## Offline / external-service boundary

- [x] Core regression tests do not require a live LLM provider.
- [x] E2E smoke test uses use_cache=false and does not depend on Redis cache data.
- [x] E2E fixture data does not depend on a live market-data provider.
- [x] E2E fixture data does not depend on a live news provider.

## Backend quality gate

Run from `backend/`:

```bash
python -m pytest -q
ruff format --check .
ruff check .
