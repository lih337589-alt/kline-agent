import type {
  ReportRead,
} from "@/lib/api";

type ReportMetaProps = {
  report: ReportRead;
};

function formatDateTime(
  value: string,
): string {
  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}

export function ReportMeta({
  report,
}: ReportMetaProps) {
  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Status
          </p>

          <p className="mt-2 text-sm font-semibold text-zinc-950">
            {report.status}
          </p>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Generated
          </p>

          <p className="mt-2 text-sm text-zinc-700">
            {formatDateTime(
              report.created_at,
            )}
          </p>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Report Source
          </p>

          <p className="mt-2 text-sm text-zinc-700">
            {report.source}
          </p>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Agent Runs
          </p>

          <p className="mt-2 text-sm text-zinc-700">
            {
              report.report
                .agent_run_ids.length
            }
          </p>
        </div>
      </div>

      <div className="mt-6 border-t border-zinc-100 pt-5">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Trace ID
        </p>

        <p className="mt-2 break-all font-mono text-xs leading-5 text-zinc-600">
          {report.trace_id}
        </p>
      </div>
    </section>
  );
}
