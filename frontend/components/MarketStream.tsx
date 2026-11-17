"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  websocketUrl,
} from "@/lib/ws";


type ConnectionStatus =
  | "connecting"
  | "connected"
  | "reconnecting";


type MarketTick = {
  type: "market_tick";
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
};


type MarketStreamProps = {
  symbol?: string;
};


function formatPrice(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-US",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(value);
}


function formatVolume(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-US",
  ).format(value);
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


function statusLabel(
  status: ConnectionStatus,
): string {
  if (
    status === "connected"
  ) {
    return "Connected";
  }

  if (
    status === "reconnecting"
  ) {
    return "Reconnecting";
  }

  return "Connecting";
}


export function MarketStream({
  symbol = "AAPL",
}: MarketStreamProps) {
  const normalizedSymbol =
    symbol.trim().toUpperCase();

  const [
    status,
    setStatus,
  ] = useState<ConnectionStatus>(
    "connecting",
  );

  const [
    latestTick,
    setLatestTick,
  ] = useState<MarketTick | null>(
    null,
  );

  const [
    recentTicks,
    setRecentTicks,
  ] = useState<MarketTick[]>(
    [],
  );

  const [
    errorMessage,
    setErrorMessage,
  ] = useState<string | null>(
    null,
  );

  useEffect(
    () => {
      let active = true;

      let socket:
        | WebSocket
        | null = null;

      let reconnectTimer:
        | ReturnType<
            typeof setTimeout
          >
        | null = null;

      function connect() {
        if (!active) {
          return;
        }

        const url =
          websocketUrl(
            `/ws/market?symbol=${encodeURIComponent(
              normalizedSymbol,
            )}`,
          );

        const nextSocket =
          new WebSocket(url);

        socket =
          nextSocket;

        nextSocket.onopen =
          () => {
            if (!active) {
              return;
            }

            setStatus(
              "connected",
            );

            setErrorMessage(
              null,
            );
          };

        nextSocket.onmessage =
          (event) => {
            if (!active) {
              return;
            }

            try {
              const payload =
                JSON.parse(
                  event.data,
                ) as MarketTick;

              if (
                payload.type
                  !==
                "market_tick"
              ) {
                return;
              }

              setLatestTick(
                payload,
              );

              setRecentTicks(
                (
                  current,
                ) => [
                  payload,
                  ...current,
                ].slice(
                  0,
                  10,
                ),
              );
            } catch {
              setErrorMessage(
                "Received an invalid market-stream message.",
              );
            }
          };

        nextSocket.onerror =
          () => {
            if (!active) {
              return;
            }

            setErrorMessage(
              "The realtime market connection encountered an error.",
            );
          };

        nextSocket.onclose =
          () => {
            if (!active) {
              return;
            }

            socket =
              null;

            setStatus(
              "reconnecting",
            );

            reconnectTimer =
              setTimeout(
                connect,
                2000,
              );
          };
      }

      connect();

      return () => {
        active = false;

        if (
          reconnectTimer
        ) {
          clearTimeout(
            reconnectTimer,
          );
        }

        if (socket) {
          socket.close();
        }
      };
    },
    [
      normalizedSymbol,
    ],
  );

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Simulated Feed
            </p>

            <h2 className="mt-2 text-xl font-semibold text-zinc-950">
              {normalizedSymbol} Realtime Market Stream
            </h2>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600">
              This Day 23 feed is generated locally for WebSocket and realtime architecture testing. It is not a live market-data source.
            </p>
          </div>

          <div className="shrink-0 rounded-full border border-zinc-200 bg-zinc-50 px-3 py-1.5 text-sm font-medium text-zinc-700">
            {statusLabel(
              status,
            )}
          </div>
        </div>

        {latestTick ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl bg-zinc-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Price
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-zinc-950">
                {formatPrice(
                  latestTick.price,
                )}
              </p>
            </div>

            <div className="rounded-xl bg-zinc-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Volume
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-zinc-950">
                {formatVolume(
                  latestTick.volume,
                )}
              </p>
            </div>

            <div className="rounded-xl bg-zinc-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                Updated
              </p>

              <p className="mt-2 text-sm leading-6 text-zinc-700">
                {formatTimestamp(
                  latestTick.timestamp,
                )}
              </p>
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-xl border border-dashed border-zinc-300 p-5">
            <p className="text-sm text-zinc-600">
              Waiting for the first market tick...
            </p>
          </div>
        )}

        {errorMessage ? (
          <div
            role="alert"
            className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4"
          >
            <p className="text-sm font-medium text-red-950">
              Realtime connection issue
            </p>

            <p className="mt-2 text-sm leading-6 text-red-900">
              {errorMessage}
            </p>

            <p className="mt-2 text-xs leading-5 text-red-800">
              The client will automatically attempt to reconnect.
            </p>
          </div>
        ) : null}
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-zinc-950">
          Recent Ticks
        </h2>

        <p className="mt-1 text-sm text-zinc-600">
          Latest 10 simulated WebSocket events.
        </p>

        {recentTicks.length > 0 ? (
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-xl text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 text-xs uppercase tracking-wider text-zinc-500">
                  <th className="px-3 py-3 font-medium">
                    Symbol
                  </th>

                  <th className="px-3 py-3 font-medium">
                    Price
                  </th>

                  <th className="px-3 py-3 font-medium">
                    Volume
                  </th>

                  <th className="px-3 py-3 font-medium">
                    Timestamp
                  </th>
                </tr>
              </thead>

              <tbody>
                {recentTicks.map(
                  (
                    tick,
                    index,
                  ) => (
                    <tr
                      key={`${tick.timestamp}-${index}`}
                      className="border-b border-zinc-100"
                    >
                      <td className="px-3 py-3 font-medium text-zinc-950">
                        {tick.symbol}
                      </td>

                      <td className="px-3 py-3 tabular-nums text-zinc-700">
                        {formatPrice(
                          tick.price,
                        )}
                      </td>

                      <td className="px-3 py-3 tabular-nums text-zinc-700">
                        {formatVolume(
                          tick.volume,
                        )}
                      </td>

                      <td className="px-3 py-3 text-zinc-600">
                        {formatTimestamp(
                          tick.timestamp,
                        )}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="mt-5 text-sm text-zinc-500">
            No realtime events received yet.
          </p>
        )}
      </section>
    </div>
  );
}
