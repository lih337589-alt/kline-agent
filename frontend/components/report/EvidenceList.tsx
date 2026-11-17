type EvidenceListProps = {
  evidenceIds: string[];
  evidenceInsufficient?: boolean;
  title?: string;
};

export function EvidenceList({
  evidenceIds,
  evidenceInsufficient = false,
  title = "Evidence",
}: EvidenceListProps) {
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          {title}
        </p>

        {evidenceInsufficient ? (
          <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-xs text-amber-900">
            Evidence insufficient
          </span>
        ) : null}
      </div>

      {evidenceIds.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-2">
          {evidenceIds.map(
            (evidenceId) => (
              <span
                key={evidenceId}
                className="rounded-full border border-zinc-200 bg-zinc-50 px-2.5 py-1 font-mono text-xs text-zinc-700"
              >
                {evidenceId}
              </span>
            ),
          )}
        </div>
      ) : (
        <p className="mt-2 text-sm text-zinc-500">
          No evidence references.
        </p>
      )}
    </div>
  );
}
