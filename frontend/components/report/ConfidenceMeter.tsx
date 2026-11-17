type ConfidenceMeterProps = {
  value: number;
  label?: string;
};

function toPercentage(
  value: number,
): number {
  const normalized = Math.min(
    1,
    Math.max(
      0,
      value,
    ),
  );

  return Math.round(
    normalized * 100,
  );
}

export function ConfidenceMeter({
  value,
  label = "Confidence",
}: ConfidenceMeterProps) {
  const percentage =
    toPercentage(value);

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          {label}
        </p>

        <p className="text-sm font-semibold tabular-nums text-zinc-950">
          {percentage}%
        </p>
      </div>

      <progress
        value={percentage}
        max={100}
        aria-label={`${label}: ${percentage}%`}
        className="mt-2 h-2 w-full overflow-hidden rounded-full"
      />
    </div>
  );
}
