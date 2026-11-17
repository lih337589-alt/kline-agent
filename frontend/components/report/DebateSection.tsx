import {
  EvidenceList,
} from "@/components/report/EvidenceList";
import type {
  BearRebuttal,
  BullClaim,
  DebateResult,
} from "@/lib/api";

type DebateSectionProps = {
  debate: DebateResult;
};

type DebatePairProps = {
  claim: BullClaim;
  rebuttal: BearRebuttal | undefined;
  index: number;
};

function DebatePair({
  claim,
  rebuttal,
  index,
}: DebatePairProps) {
  return (
    <article className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm">
      <div className="border-b border-zinc-100 bg-zinc-50 px-6 py-4">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Debate Point {index + 1}
        </p>

        <p className="mt-1 font-mono text-xs text-zinc-500">
          {claim.claim_id}
        </p>
      </div>

      <div className="grid lg:grid-cols-2">
        <section className="p-6 lg:border-r lg:border-zinc-100">
          <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
            Bull Case
          </p>

          <h3 className="mt-3 text-lg font-semibold leading-7 text-zinc-950">
            {claim.claim}
          </h3>

          <div className="mt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Rationale
            </p>

            <p className="mt-2 text-sm leading-6 text-zinc-700">
              {claim.rationale}
            </p>
          </div>

          <div className="mt-5 border-t border-zinc-100 pt-5">
            <EvidenceList
              evidenceIds={
                claim.evidence_ids
              }
              evidenceInsufficient={
                claim.evidence_insufficient
              }
            />
          </div>
        </section>

        <section className="border-t border-zinc-100 p-6 lg:border-t-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-red-700">
            Bear Rebuttal
          </p>

          {rebuttal ? (
            <>
              <p className="mt-3 text-sm leading-6 text-zinc-700">
                {
                  rebuttal.counter_argument
                }
              </p>

              <p className="mt-3 font-mono text-xs text-zinc-500">
                Rebuttal ID:{" "}
                {
                  rebuttal.rebuttal_id
                }
              </p>

              <div className="mt-5 border-t border-zinc-100 pt-5">
                <EvidenceList
                  evidenceIds={
                    rebuttal.evidence_ids
                  }
                  evidenceInsufficient={
                    rebuttal.evidence_insufficient
                  }
                />
              </div>
            </>
          ) : (
            <p className="mt-3 text-sm text-zinc-500">
              No matching bear rebuttal was returned.
            </p>
          )}
        </section>
      </div>
    </article>
  );
}

export function DebateSection({
  debate,
}: DebateSectionProps) {
  const rebuttalsByClaimId =
    new Map(
      debate.bear_rebuttals.map(
        (rebuttal) => [
          rebuttal.bull_claim_id,
          rebuttal,
        ],
      ),
    );

  return (
    <section>
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Adversarial Analysis
        </p>

        <h2 className="mt-2 text-2xl font-semibold text-zinc-950">
          Bull vs Bear Debate
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-600">
          Each bullish claim is shown beside the corresponding bearish rebuttal so that conflicting interpretations remain visible.
        </p>
      </div>

      <div className="mt-6 space-y-5">
        {debate.bull_claims.map(
          (
            claim,
            index,
          ) => (
            <DebatePair
              key={claim.claim_id}
              claim={claim}
              rebuttal={
                rebuttalsByClaimId.get(
                  claim.claim_id,
                )
              }
              index={index}
            />
          ),
        )}
      </div>

      <div className="mt-6 rounded-2xl border border-zinc-200 bg-zinc-50 p-6">
        <h3 className="text-base font-semibold text-zinc-950">
          Unresolved Questions
        </h3>

        {debate.unresolved_questions.length >
        0 ? (
          <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-700">
            {debate.unresolved_questions.map(
              (
                question,
                index,
              ) => (
                <li
                  key={`debate-question-${index}`}
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
            No unresolved debate questions were reported.
          </p>
        )}
      </div>
    </section>
  );
}
