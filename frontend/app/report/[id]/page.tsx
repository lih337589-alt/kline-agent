import {
  AgentCard,
} from "@/components/report/AgentCard";
import {
  CrossExamSection,
} from "@/components/report/CrossExamSection";
import {
  DebateSection,
} from "@/components/report/DebateSection";
import {
  EvidenceList,
} from "@/components/report/EvidenceList";
import {
  JudgmentSection,
} from "@/components/report/JudgmentSection";
import {
  ReportMeta,
} from "@/components/report/ReportMeta";
import { PageShell } from "@/components/PageShell";
import {
  ApiRequestError,
  getReport,
} from "@/lib/api";
import type {
  ReportRead,
} from "@/lib/api";

type ReportPageProps = {
  params: Promise<{
    id: string;
  }>;
};

type ReportErrorStateProps = {
  title: string;
  message: string;
  detail: string;
};

function ReportErrorState({
  title,
  message,
  detail,
}: ReportErrorStateProps) {
  return (
    <PageShell
      title={title}
      description="Unable to load this research report."
    >
      <section className="rounded-2xl border border-red-200 bg-red-50 p-6">
        <h2 className="text-lg font-semibold text-red-950">
          {message}
        </h2>

        <p className="mt-3 text-sm leading-6 text-red-900">
          {detail}
        </p>
      </section>
    </PageShell>
  );
}

export default async function ReportPage({
  params,
}: ReportPageProps) {
  const { id } = await params;

  const reportId =
    Number(id);

  if (
    !Number.isInteger(reportId) ||
    reportId <= 0
  ) {
    return (
      <ReportErrorState
        title={`Report ${id}`}
        message="Invalid report ID"
        detail="The report ID must be a positive integer."
      />
    );
  }

  let report: ReportRead | null =
    null;

  let loadError: unknown =
    null;

  try {
    report = await getReport(
      reportId,
    );
  } catch (error) {
    loadError = error;
  }

  if (
    loadError !== null ||
    report === null
  ) {
    const isNotFound =
      loadError instanceof
        ApiRequestError &&
      loadError.status === 404;

    const detail =
      loadError instanceof Error
        ? loadError.message
        : "Unknown API error.";

    return (
      <ReportErrorState
        title={`Report ${reportId}`}
        message={
          isNotFound
            ? "Report not found"
            : "Backend data unavailable"
        }
        detail={
          isNotFound
            ? detail
            : `${detail} Confirm that the FastAPI backend is running on port 8000, then reload this page.`
        }
      />
    );
  }

  const payload =
    report.report;

  const agents = [
    {
      key: "fundamental",
      title:
        "Fundamental Agent",
      result:
        payload.fundamental,
    },
    {
      key: "valuation",
      title:
        "Valuation Agent",
      result:
        payload.valuation,
    },
    {
      key: "technical",
      title:
        "Technical Agent",
      result:
        payload.technical,
    },
    {
      key: "sentiment",
      title:
        "Sentiment Agent",
      result:
        payload.sentiment,
    },
    {
      key: "risk",
      title:
        "Risk Agent",
      result:
        payload.risk,
    },
  ];

  return (
    <PageShell
      title={report.title}
      description={`${payload.company_name} · ${report.symbol}`}
    >
      <ReportMeta
        report={report}
      />

      <section className="mt-8 rounded-2xl border border-zinc-200 bg-zinc-950 p-7 text-white shadow-sm sm:p-8">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Executive Summary
        </p>

        <h2 className="mt-2 text-2xl font-semibold">
          Research Overview
        </h2>

        <p className="mt-4 max-w-5xl text-sm leading-7 text-zinc-200">
          {
            payload.executive_summary
          }
        </p>
      </section>

      <section className="mt-10">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Multi-Agent Analysis
          </p>

          <h2 className="mt-2 text-2xl font-semibold text-zinc-950">
            Professional Agent Views
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-600">
            Five specialist agents evaluate the company from different analytical perspectives.
          </p>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          {agents.map(
            (agent) => (
              <AgentCard
                key={agent.key}
                title={
                  agent.title
                }
                result={
                  agent.result
                }
              />
            ),
          )}
        </div>
      </section>

      <div className="my-12 border-t border-zinc-200" />

      <DebateSection
        debate={
          payload.debate
        }
      />

      <div className="my-12 border-t border-zinc-200" />

      <CrossExamSection
        result={
          payload.cross_exam
        }
      />

      <div className="my-12 border-t border-zinc-200" />

      <JudgmentSection
        judgment={
          payload.judgment
        }
      />

      <section className="mt-10 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Report Evidence
        </p>

        <h2 className="mt-2 text-xl font-semibold text-zinc-950">
          Global Evidence References
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-600">
          These identifiers are the evidence references collected from the five professional agents.
        </p>

        <div className="mt-5">
          <EvidenceList
            evidenceIds={
              payload.sources
            }
            title="Sources"
          />
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-amber-200 bg-amber-50 p-6">
        <p className="text-xs font-medium uppercase tracking-wider text-amber-800">
          Important
        </p>

        <h2 className="mt-2 text-lg font-semibold text-amber-950">
          Research Disclaimer
        </h2>

        <p className="mt-3 text-sm leading-6 text-amber-900">
          This AI-generated report is provided for research and informational purposes only. It does not constitute investment advice, a recommendation, an offer, or a solicitation to buy or sell any security. The report may contain incomplete, delayed, synthetic, or uncertain data. Review the underlying evidence and conduct independent research before making financial decisions.
        </p>
      </section>
    </PageShell>
  );
}
