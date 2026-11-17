"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  getRiskAlerts,
  type RiskAlertRead,
  type RiskSeverity,
} from "@/lib/api";


type RiskAlertsProps = {
  symbol?: string;
};


function formatAlertType(
  value: string,
): string {
  return value
    .replaceAll(
      "_",
      " ",
    )
    .toUpperCase();
}


function formatTimestamp(
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
      timeStyle: "medium",
    },
  ).format(date);
}


function cardClass(
  severity: RiskSeverity,
): string {
  if (severity === "high") {
    return "border-red-200 bg-red-50";
  }

  if (severity === "medium") {
    return "border-orange-200 bg-orange-50";
  }

  return "border-amber-200 bg-amber-50";
}


function badgeClass(
  severity: RiskSeverity,
): string {
  if (severity === "high") {
    return "border-red-300 bg-red-100 text-red-800";
  }

  if (severity === "medium") {
    return "border-orange-300 bg-orange-100 text-orange-800";
  }

  return "border-amber-300 bg-amber-100 text-amber-800";
}


function AlertCard({
  alert,
}: {
  alert: RiskAlertRead;
}) {
  return (
    <article
      className={`rounded-2xl border p-5 ${cardClass(
        alert.severity,
      )}`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-wider ${badgeClass(
                alert.severity,
              )}`}
            >
              {alert.severity}
            </span>

            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-600">
              {formatAlertType(
                alert.alert_type,
              )}
            </span>
          </div>

          <h3 className="mt-3 text-lg font-semibold text-zinc-950">
            {alert.symbol}
          </h3>
        </div>

        <time className="text-xs text-zinc-600">
          {formatTimestamp(
            alert.event_time,
          )}
        </time>
      </div>

      <p className="mt-4 text-sm leading-6 text-zinc-800">
        {alert.message}
      </p>

      {alert.explanation ? (
        <div className="mt-5 space-y-4 border-t border-black/10 pt-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-600">
              Reason
            </p>

            <p className="mt-1 text-sm leading-6 text-zinc-800">
              {alert.explanation.reason}
            </p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-600">
              Impact Path
            </p>

            <ul className="mt-2 space-y-1 text-sm text-zinc-800">
              {alert.explanation.impact_path.map(
                (
                  item,
                  index,
                ) => (
                  <li
                    key={`${alert.id}-impact-${index}`}
                  >
                    • {item}
                  </li>
                ),
              )}
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-600">
              Uncertainty
            </p>

            <p className="mt-1 text-sm leading-6 text-zinc-800">
              {alert.explanation.uncertainty}
            </p>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-600">
              Suggested Attention
            </p>

            <ul className="mt-2 space-y-1 text-sm text-zinc-800">
              {alert.explanation.suggested_attention.map(
                (
                  item,
                  index,
                ) => (
                  <li
                    key={`${alert.id}-attention-${index}`}
                  >
                    • {item}
                  </li>
                ),
              )}
            </ul>
          </div>
        </div>
      ) : (
        <p className="mt-4 border-t border-black/10 pt-4 text-xs leading-5 text-zinc-600">
          Deterministic rule alert. AI explanation is not attached to this alert yet.
        </p>
      )}
    </article>
  );
}


export function RiskAlerts({
  symbol = "AAPL",
}: RiskAlertsProps) {
  const [
    alerts,
    setAlerts,
  ] = useState<RiskAlertRead[]>(
    [],
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  useEffect(
    () => {
      let active = true;

      async function loadAlerts() {
        try {
          const result =
            await getRiskAlerts(
              symbol,
              20,
            );

          if (!active) {
            return;
          }

          setAlerts(
            result.alerts,
          );

          setErrorMessage(
            null,
          );
        } catch (error) {
          if (!active) {
            return;
          }

          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Unable to load risk alerts.",
          );
        } finally {
          if (active) {
            setLoading(false);
          }
        }
      }

      void loadAlerts();

      const timer =
        window.setInterval(
          () => {
            void loadAlerts();
          },
          5000,
        );

      return () => {
        active = false;

        window.clearInterval(
          timer,
        );
      };
    },
    [
      symbol,
    ],
  );

  return (
    <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
            Risk Monitoring
          </p>

          <h2 className="mt-2 text-xl font-semibold text-zinc-950">
            {symbol.toUpperCase()} Risk Alerts
          </h2>

          <p className="mt-2 text-sm leading-6 text-zinc-600">
            Deterministic risk alerts generated from the realtime rule engine. This list refreshes automatically every 5 seconds.
          </p>
        </div>

        <div className="rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-sm font-medium text-zinc-700">
          {alerts.length} alerts
        </div>
      </div>

      {loading ? (
        <div className="mt-6 rounded-xl border border-dashed border-zinc-300 p-5">
          <p className="text-sm text-zinc-600">
            Loading risk alerts...
          </p>
        </div>
      ) : null}

      {errorMessage ? (
        <div
          role="alert"
          className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4"
        >
          <p className="text-sm font-medium text-red-950">
            Unable to load risk alerts
          </p>

          <p className="mt-2 text-sm text-red-900">
            {errorMessage}
          </p>
        </div>
      ) : null}

      {!loading &&
      !errorMessage &&
      alerts.length === 0 ? (
        <div className="mt-6 rounded-xl border border-dashed border-zinc-300 p-5">
          <p className="text-sm font-medium text-zinc-900">
            No recent risk alerts
          </p>

          <p className="mt-2 text-sm leading-6 text-zinc-600">
            No configured risk rule has produced an alert for this symbol yet.
          </p>
        </div>
      ) : null}

      {alerts.length > 0 ? (
        <div className="mt-6 space-y-4">
          {alerts.map(
            (alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
              />
            ),
          )}
        </div>
      ) : null}

      <p className="mt-6 text-xs leading-5 text-zinc-500">
        Risk alerts are informational research signals and do not execute or recommend trades.
      </p>
    </section>
  );
}
