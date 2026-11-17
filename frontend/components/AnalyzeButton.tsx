"use client";

import {
  useState,
} from "react";
import {
  useRouter,
} from "next/navigation";

import {
  createAnalysis,
} from "@/lib/api";

type AnalyzeButtonProps = {
  symbol: string;
};

export function AnalyzeButton({
  symbol,
}: AnalyzeButtonProps) {
  const router = useRouter();

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  async function runAnalysis() {
    if (isLoading) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const result =
        await createAnalysis({
          symbol,
          use_cache: true,
        });

      router.push(
        `/report/${result.report_id}`,
      );
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unknown analysis error.";

      setErrorMessage(
        message,
      );

      setIsLoading(false);
    }
  }

  return (
    <div className="w-full lg:max-w-sm">
      <button
        type="button"
        onClick={runAnalysis}
        disabled={isLoading}
        className="min-h-11 w-full rounded-xl bg-zinc-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
      >
        {isLoading
          ? `Analyzing ${symbol}...`
          : "Run Multi-Agent Analysis"}
      </button>

      {isLoading ? (
        <div
          role="status"
          aria-live="polite"
          className="mt-4 rounded-xl border border-blue-200 bg-blue-50 p-4"
        >
          <p className="text-sm font-medium text-blue-950">
            Analysis in progress
          </p>

          <p className="mt-2 text-sm leading-6 text-blue-900">
            The multi-agent workflow is running. Several AI analysis steps must finish before the final report is generated.
          </p>
        </div>
      ) : null}

      {errorMessage ? (
        <div
          role="alert"
          className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4"
        >
          <p className="text-sm font-semibold text-red-950">
            Analysis failed
          </p>

          <p className="mt-2 break-words text-sm leading-6 text-red-900">
            {errorMessage}
          </p>

          <button
            type="button"
            onClick={runAnalysis}
            className="mt-4 rounded-lg border border-red-300 bg-white px-4 py-2 text-sm font-medium text-red-900 transition hover:bg-red-100"
          >
            Try Again
          </button>
        </div>
      ) : null}
    </div>
  );
}
