import { PageShell } from "@/components/PageShell";
import { StockSearch } from "@/components/StockSearch";

export default function DashboardPage() {
  return (
    <PageShell
      title="Dashboard"
      description="输入股票代码进入行情与研究页面。"
    >
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-zinc-950">
          Stock Research
        </p>

        <p className="mt-2 text-sm leading-6 text-zinc-600">
          输入股票代码，例如 AAPL、MSFT 或 NVDA。
        </p>

        <div className="mt-5">
          <StockSearch />
        </div>
      </section>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-zinc-200 bg-white p-6">
          <p className="text-sm font-medium text-zinc-950">
            Reports
          </p>

          <p className="mt-2 text-sm leading-6 text-zinc-600">
            已生成的多智能体报告将在 Day 21
            完整接入前端。
          </p>
        </section>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6">
          <p className="text-sm font-medium text-zinc-950">
            Risk Alerts
          </p>

          <p className="mt-2 text-sm leading-6 text-zinc-600">
            实时风险事件将在后续风险阶段接入。
          </p>
        </section>
      </div>
    </PageShell>
  );
}
