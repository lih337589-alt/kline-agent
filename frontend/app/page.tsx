import Link from "next/link";

import { PageShell } from "@/components/PageShell";

const destinations = [
  {
    href: "/dashboard",
    title: "Dashboard",
    description: "进入多智能体金融研究工作台。",
  },
  {
    href: "/stock/AAPL",
    title: "Stock",
    description: "查看股票详情页面骨架。",
  },
  {
    href: "/report/1",
    title: "Report",
    description: "查看结构化多智能体研究报告页面骨架。",
  },
  {
    href: "/alerts",
    title: "Alerts",
    description: "查看实时风险提醒页面骨架。",
  },
];

export default function Home() {
  return (
    <PageShell
      title="K线之上"
      description="AI 多智能体金融研究 MVP。后端分析工作流已经跑通，现在开始建立正式用户界面。"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {destinations.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:border-zinc-300 hover:shadow-md"
          >
            <h2 className="text-lg font-semibold text-zinc-950">
              {item.title}
            </h2>

            <p className="mt-2 text-sm leading-6 text-zinc-600">
              {item.description}
            </p>
          </Link>
        ))}
      </div>

      <section className="mt-8 rounded-2xl border border-zinc-200 bg-white p-6">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          MVP Scope
        </p>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-700">
          专业 Agent、Bull/Bear 辩论、Cross Examiner 和 Judge
          已由后端工作流生成结构化研究结果。前端将在后续阶段逐步接入行情、报告和风险事件。
        </p>
      </section>
    </PageShell>
  );
}
