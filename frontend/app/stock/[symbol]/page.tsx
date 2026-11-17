import {
  AnalyzeButton,
} from "@/components/AnalyzeButton";
import {
  PageShell,
} from "@/components/PageShell";
import {
  PriceChart,
} from "@/components/PriceChart";
import {
  StockSearch,
} from "@/components/StockSearch";
import {
  ApiRequestError,
  getStock,
  getStockPrices,
} from "@/lib/api";
import type {
  StockPriceSeries,
  StockRead,
} from "@/lib/api";

type StockPageProps = {
  params: Promise<{
    symbol: string;
  }>;
};

function formatPrice(
  value: number | null | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return new Intl.NumberFormat(
    "en-US",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(value);
}

function formatVolume(
  value: number | null | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
}

function formatTimestamp(
  value: string | null,
): string {
  if (!value) {
    return "No data";
  }

  return new Intl.DateTimeFormat(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(
    new Date(value),
  );
}

export default async function StockPage({
  params,
}: StockPageProps) {
  const { symbol } = await params;

  const normalizedSymbol =
    symbol.trim().toUpperCase();

  let stock: StockRead | null = null;
  let priceSeries: StockPriceSeries | null = null;
  let loadError: unknown = null;

  try {
    [
      stock,
      priceSeries,
    ] = await Promise.all([
      getStock(
        normalizedSymbol,
      ),
      getStockPrices(
        normalizedSymbol,
        120,
      ),
    ]);
  } catch (error) {
    loadError = error;
  }

  if (
    loadError !== null ||
    stock === null ||
    priceSeries === null
  ) {
    const isNotFound =
      loadError instanceof ApiRequestError &&
      loadError.status === 404;

    const message =
      loadError instanceof Error
        ? loadError.message
        : "Unknown API error.";

    return (
      <PageShell
        title={normalizedSymbol}
        description="Unable to load stock data."
      >
        <StockSearch
          initialSymbol={
            normalizedSymbol
          }
        />

        <section className="mt-8 rounded-2xl border border-red-200 bg-red-50 p-6">
          <h2 className="text-lg font-semibold text-red-950">
            {isNotFound
              ? "Stock not found"
              : "Backend data unavailable"}
          </h2>

          <p className="mt-2 text-sm leading-6 text-red-900">
            {message}
          </p>

          <p className="mt-3 text-sm leading-6 text-red-800">
            {isNotFound
              ? "Check the symbol and try again."
              : "Confirm that the FastAPI backend is running on port 8000, then reload this page."}
          </p>
        </section>
      </PageShell>
    );
  }

  const latestPrice =
    priceSeries.prices[
      priceSeries.prices.length - 1
    ];

  return (
    <PageShell
      title={stock.symbol}
      description={stock.name}
    >
      <StockSearch
        initialSymbol={
          stock.symbol
        }
      />

      <section className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              AI Research
            </p>

            <h2 className="mt-2 text-xl font-semibold text-zinc-950">
              Multi-Agent Analysis
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              Run the five specialist agents, adversarial Bull/Bear debate, cross examination, and final judge synthesis for{" "}
              {stock.symbol}.
            </p>

            <p className="mt-2 max-w-2xl text-xs leading-5 text-zinc-500">
              Analysis output depends on the currently available market, financial, and text evidence and may include data-quality limitations.
            </p>
          </div>

          <div className="w-full shrink-0 lg:w-auto">
            <AnalyzeButton
              symbol={
                stock.symbol
              }
            />
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-zinc-200 bg-white p-5">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Latest Close
          </p>

          <p className="mt-3 text-2xl font-semibold text-zinc-950">
            {latestPrice
              ? formatPrice(
                  latestPrice.close,
                )
              : "—"}
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white p-5">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Volume
          </p>

          <p className="mt-3 text-2xl font-semibold text-zinc-950">
            {latestPrice
              ? formatVolume(
                  latestPrice.volume,
                )
              : "—"}
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white p-5">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Exchange
          </p>

          <p className="mt-3 text-lg font-semibold text-zinc-950">
            {stock.exchange ?? "—"}
          </p>
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white p-5">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Industry
          </p>

          <p className="mt-3 text-lg font-semibold text-zinc-950">
            {stock.industry ?? "—"}
          </p>
        </div>
      </section>

      <section className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-zinc-100 pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-950">
              Price & Volume
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Latest{" "}
              {priceSeries.count}{" "}
              available price points.
            </p>
          </div>

          <div className="text-sm text-zinc-500 sm:text-right">
            <p>
              Updated:{" "}
              {formatTimestamp(
                priceSeries.latest_timestamp,
              )}
            </p>

            <p className="mt-1">
              Source:{" "}
              {priceSeries.sources.length
                ? priceSeries.sources.join(
                    ", ",
                  )
                : "Unknown"}
            </p>
          </div>
        </div>

        <div className="pt-4">
          <PriceChart
            prices={
              priceSeries.prices
            }
          />
        </div>
      </section>

      {priceSeries.count < 20 ? (
        <section className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <p className="text-sm font-medium text-amber-950">
            Limited price history
          </p>

          <p className="mt-2 text-sm leading-6 text-amber-900">
            This symbol currently has only{" "}
            {priceSeries.count}{" "}
            price point
            {priceSeries.count === 1
              ? ""
              : "s"}
            . Longer-history technical interpretation may be limited.
          </p>
        </section>
      ) : null}
    </PageShell>
  );
}
