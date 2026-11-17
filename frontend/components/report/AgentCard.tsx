import {
  ConfidenceMeter,
} from "@/components/report/ConfidenceMeter";
import {
  EvidenceList,
} from "@/components/report/EvidenceList";
import type {
  AgentResult,
} from "@/lib/api";

type AgentCardProps = {
  title: string;
  result: AgentResult;
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
      <h4 className="text-sm font-semibold text-zinc-950">
        {title}
      </h4>

      {items.length > 0 ? (
        <ul className="mt-2 space-y-2 text-sm leading-6 text-zinc-700">
          {items.map(
            (item, index) => (
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
        <p className="mt-2 text-sm text-zinc-500">
          {emptyText}
        </p>
      )}
    </div>
  );
}

export function AgentCard({
  title,
  result,
}: AgentCardProps) {
  return (
    <article className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="border-b border-zinc-100 pb-5">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Professional Agent
        </p>

        <h3 className="mt-2 text-xl font-semibold text-zinc-950">
          {title}
        </h3>

        <p className="mt-3 text-sm leading-6 text-zinc-700">
          {result.summary}
        </p>
      </div>

      <div className="mt-5">
        <ConfidenceMeter
          value={result.confidence}
        />
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <TextList
          title="Positives"
          items={result.positives}
          emptyText="No positive points reported."
        />

        <TextList
          title="Negatives"
          items={result.negatives}
          emptyText="No negative points reported."
        />
      </div>

      <div className="mt-6 border-t border-zinc-100 pt-5">
        <EvidenceList
          evidenceIds={
            result.evidence_ids
          }
        />
      </div>

      <div className="mt-6 border-t border-zinc-100 pt-5">
        <TextList
          title="Limitations"
          items={result.limitations}
          emptyText="No limitations reported."
        />
      </div>
    </article>
  );
}
