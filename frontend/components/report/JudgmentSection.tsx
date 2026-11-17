import {
  ConfidenceMeter,
} from "@/components/report/ConfidenceMeter";
import {
  EvidenceList,
} from "@/components/report/EvidenceList";
import type {
  JudgeDecision,
  JudgeResult,
} from "@/lib/api";

type JudgmentSectionProps = {
  judgment: JudgeResult;
};

type TextListProps = {
  title: string;
  items: string[];
  emptyText: string;
};

function TextList({
  title,
  items,
  emptyText,
}: TextListProps) {
  return (
    <div>
      <h3 className="text-base font-semibold text-zinc-950">
        {title}
      </h3>

      {items.length > 0 ? (
        <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-700">
          {items.map(
            (
              item,
              index,
            ) => (
              <li
                key={`${title}-${index}`}
                className="flex gap-2"
              >
                <span
                  aria-hidden="true"
                  className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-zinc-400"
                />

                <span>
                  {item}
                </span>
              </li>
            ),
          )}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-zinc-500">
          {emptyText}
        </p>
      )}
    </div>
  );
}

function formatDecision(
  decision: JudgeDecision,
): string {
  const labels: Record<
    JudgeDecision,
    string
  > = {
    accepted:
      "Accepted",
    rejected:
      "Rejected",
    partially_accepted:
      "Partially Accepted",
    uncertain:
      "Uncertain",
  };

  return labels[decision];
}

function decisionClasses(
  decision: JudgeDecision,
): string {
  if (decision === "accepted") {
    return "border-emerald-200 bg-emerald-50 text-emerald-900";
  }

  if (decision === "rejected") {
    return "border-red-200 bg-red-50 text-red-900";
  }

  if (
    decision ===
    "partially_accepted"
  ) {
    return "border-blue-200 bg-blue-50 text-blue-900";
  }

  return "border-amber-200 bg-amber-50 text-amber-900";
}

export function JudgmentSection({
  judgment,
}: JudgmentSectionProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-zinc-300 bg-white shadow-sm">
      <header className="border-b border-zinc-200 bg-zinc-950 px-6 py-7 text-white sm:px-8">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Final Synthesis
        </p>

        <h2 className="mt-2 text-2xl font-semibold">
          Judge Assessment
        </h2>

        <p className="mt-4 max-w-4xl text-sm leading-7 text-zinc-200">
          {judgment.overall_view}
        </p>
      </header>

      <div className="p-6 sm:p-8">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-5">
            <ConfidenceMeter
              value={
                judgment.confidence
              }
              label="Judge Confidence"
            />
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-5">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Data Freshness
            </p>

            <p className="mt-3 text-sm leading-6 text-zinc-700">
              {
                judgment.data_freshness
              }
            </p>
          </div>
        </div>

        <div className="mt-8 grid gap-8 lg:grid-cols-2">
          <TextList
            title="Key Drivers"
            items={
              judgment.key_drivers
            }
            emptyText="No key drivers were reported."
          />

          <TextList
            title="Key Risks"
            items={
              judgment.key_risks
            }
            emptyText="No key risks were reported."
          />
        </div>

        <div className="mt-8 border-t border-zinc-200 pt-8">
          <TextList
            title="Key Disputes"
            items={
              judgment.disputes
            }
            emptyText="No disputes were reported."
          />
        </div>

        <div className="mt-8 border-t border-zinc-200 pt-8">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Evidence Review
            </p>

            <h3 className="mt-2 text-xl font-semibold text-zinc-950">
              Point Assessments
            </h3>

            <p className="mt-2 text-sm leading-6 text-zinc-600">
              The judge evaluates individual debate points and records how strongly each point is supported.
            </p>
          </div>

          <div className="mt-5 space-y-4">
            {judgment.point_assessments.map(
              (
                assessment,
                index,
              ) => (
                <article
                  key={
                    assessment.point_id
                  }
                  className="rounded-2xl border border-zinc-200 p-5"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                        Assessment{" "}
                        {index + 1}
                      </p>

                      <p className="mt-2 font-mono text-xs text-zinc-500">
                        {
                          assessment.point_id
                        }
                      </p>
                    </div>

                    <span
                      className={`w-fit rounded-full border px-3 py-1 text-xs font-medium ${decisionClasses(
                        assessment.decision,
                      )}`}
                    >
                      {formatDecision(
                        assessment.decision,
                      )}
                    </span>
                  </div>

                  <p className="mt-4 text-sm leading-6 text-zinc-700">
                    {
                      assessment.reason
                    }
                  </p>

                  <div className="mt-5 border-t border-zinc-100 pt-5">
                    <EvidenceList
                      evidenceIds={
                        assessment.evidence_ids
                      }
                      evidenceInsufficient={
                        assessment.evidence_insufficient
                      }
                    />
                  </div>
                </article>
              ),
            )}
          </div>
        </div>

        <div className="mt-8 border-t border-zinc-200 pt-8">
          <TextList
            title="Judge Limitations"
            items={
              judgment.limitations
            }
            emptyText="No judge limitations were reported."
          />
        </div>
      </div>
    </section>
  );
}
