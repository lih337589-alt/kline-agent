import {
  EvidenceList,
} from "@/components/report/EvidenceList";
import type {
  CrossExamResult,
  CrossIssueCategory,
  IssueSeverity,
} from "@/lib/api";

type CrossExamSectionProps = {
  result: CrossExamResult;
};

function formatCategory(
  category: CrossIssueCategory,
): string {
  const labels: Record<
    CrossIssueCategory,
    string
  > = {
    date_conflict: "Date Conflict",
    evidence_gap: "Evidence Gap",
    logic_gap: "Logic Gap",
    metric_mismatch: "Metric Mismatch",
    data_quality: "Data Quality",
    other: "Other",
  };

  return labels[category];
}

function formatSeverity(
  severity: IssueSeverity,
): string {
  const labels: Record<
    IssueSeverity,
    string
  > = {
    low: "Low",
    medium: "Medium",
    high: "High",
  };

  return labels[severity];
}

function severityClasses(
  severity: IssueSeverity,
): string {
  if (severity === "high") {
    return "border-red-200 bg-red-50 text-red-900";
  }

  if (severity === "medium") {
    return "border-amber-200 bg-amber-50 text-amber-900";
  }

  return "border-zinc-200 bg-zinc-50 text-zinc-700";
}

export function CrossExamSection({
  result,
}: CrossExamSectionProps) {
  return (
    <section>
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Independent Review
        </p>

        <h2 className="mt-2 text-2xl font-semibold text-zinc-950">
          Cross Examination
        </h2>

        <p className="mt-3 max-w-4xl text-sm leading-6 text-zinc-700">
          {result.summary}
        </p>
      </div>

      <div className="mt-6 space-y-4">
        {result.issues.length > 0 ? (
          result.issues.map(
            (
              issue,
              index,
            ) => (
              <article
                key={issue.issue_id}
                className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Issue {index + 1}
                    </p>

                    <h3 className="mt-2 text-lg font-semibold text-zinc-950">
                      {formatCategory(
                        issue.category,
                      )}
                    </h3>
                  </div>

                  <span
                    className={`w-fit rounded-full border px-3 py-1 text-xs font-medium ${severityClasses(
                      issue.severity,
                    )}`}
                  >
                    {formatSeverity(
                      issue.severity,
                    )}{" "}
                    severity
                  </span>
                </div>

                <p className="mt-4 text-sm leading-6 text-zinc-700">
                  {issue.description}
                </p>

                {issue.related_ids.length > 0 ? (
                  <div className="mt-5">
                    <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Related Points
                    </p>

                    <div className="mt-2 flex flex-wrap gap-2">
                      {issue.related_ids.map(
                        (relatedId) => (
                          <span
                            key={relatedId}
                            className="rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 font-mono text-xs text-zinc-700"
                          >
                            {relatedId}
                          </span>
                        ),
                      )}
                    </div>
                  </div>
                ) : null}

                <div className="mt-5 border-t border-zinc-100 pt-5">
                  <EvidenceList
                    evidenceIds={
                      issue.evidence_ids
                    }
                    evidenceInsufficient={
                      issue.evidence_insufficient
                    }
                  />
                </div>
              </article>
            ),
          )
        ) : (
          <div className="rounded-2xl border border-zinc-200 bg-white p-6">
            <p className="text-sm text-zinc-500">
              No cross-examination issues were reported.
            </p>
          </div>
        )}
      </div>

      <div className="mt-6 rounded-2xl border border-zinc-200 bg-zinc-50 p-6">
        <h3 className="text-base font-semibold text-zinc-950">
          Unresolved Questions
        </h3>

        {result.unresolved_questions.length > 0 ? (
          <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-700">
            {result.unresolved_questions.map(
              (
                question,
                index,
              ) => (
                <li
                  key={`cross-question-${index}`}
                  className="flex gap-2"
                >
                  <span
                    aria-hidden="true"
                    className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-zinc-400"
                  />

                  <span>
                    {question}
                  </span>
                </li>
              ),
            )}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-zinc-500">
            No unresolved cross-examination questions were reported.
          </p>
        )}
      </div>
    </section>
  );
}
