# K线之上 · kline-agent

AI 多智能体金融研究平台。多个专职 Agent（基本面、估值、技术面、情绪、风险）协同分析个股，经多空辩论与交叉质询后由裁判 Agent 汇总成一份结构化研究报告，同时通过 WebSocket 推送实时行情与风控告警。

## 技术栈

**后端** — Python 3.13 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 · Alembic · PostgreSQL 17 · Redis 7 · LangGraph · pandas / numpy · pytest

**前端** — Next.js 16（App Router）· React 19 · TypeScript · Tailwind CSS v4 · ECharts 6

**部署** — Docker Compose，四个服务（前端 / 后端 / PostgreSQL / Redis）均带健康检查与依赖顺序

## 架构

```
frontend (Next.js :3000)
        │  REST + WebSocket
backend (FastAPI :8000)
        ├── api/          路由层
        ├── services/     业务逻辑、特征工程、报告生成
        ├── repositories/ 数据访问
        ├── agents/       五个分析 Agent + bull/bear/judge/cross_examiner
        ├── workflows/    LangGraph 状态图编排
        ├── risk/         规则引擎与告警解释
        └── realtime/     行情流与 WebSocket 广播
        │
   PostgreSQL 17      Redis 7
```

分析流程：`fundamental → valuation → technical → sentiment → risk`，随后进入多空辩论与裁判汇总。

## 快速开始

### 1. 配置环境变量

密钥只放在本地 `.env` 中，**不要提交到仓库**（`.gitignore` 已排除，pre-commit 钩子也会拦截）。

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填入你自己的密钥：

| 变量 | 说明 |
| --- | --- |
| `LLM_PROVIDER` | `deepseek` / `openai` / `demo`。`demo` 使用内置假客户端，无需密钥即可跑通全流程 |
| `LLM_BASE_URL` | 兼容 OpenAI 协议的服务地址，如 `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名 |
| `LLM_API_KEY` | 你的密钥，留空则需用 `demo` 模式 |
| `ALPHA_VANTAGE_API_KEY` | 可选，行情数据源 |
| `DATABASE_URL` | 本地直跑时使用；Docker 启动由 compose 覆盖 |

前端如需指向非默认后端地址：

```bash
cp frontend/.env.local.example frontend/.env.local
```

### 2. 启动

一键启动全部服务：

```bash
docker compose up -d
```

- 前端 http://localhost:3000
- 后端 http://localhost:8000
- 接口文档 http://localhost:8000/docs

首次启动会自动执行 Alembic 迁移。导入演示数据：

```bash
docker compose exec backend python -m scripts.seed_demo
```

### 3. 本地开发（不用 Docker）

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## 测试

```bash
docker compose cp backend/tests backend:/app/tests
docker compose exec backend python -m pytest -q
```

## 主要接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/stocks` | 标的列表 |
| GET | `/api/stocks/{symbol}` | 标的基本信息 |
| GET | `/api/stocks/{symbol}/prices` | 历史行情 |
| POST | `/api/analyses` | 发起一次多智能体分析 |
| GET | `/api/reports/{report_id}` | 获取研究报告 |
| GET | `/api/alerts` | 风控告警 |
| WS | `/ws/market` | 实时行情推送 |

## 安全约定

- 所有密钥通过环境变量注入，代码中不设默认值
- `.env` 文件永不入库，仅提交 `.env.example`
- 提交前钩子会拦截 `.env` 与常见格式的硬编码密钥

启用提交钩子：

```bash
git config core.hooksPath .githooks
```
