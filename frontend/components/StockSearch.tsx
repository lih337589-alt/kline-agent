"use client";

import {
  FormEvent,
  useState,
} from "react";
import { useRouter } from "next/navigation";

type StockSearchProps = {
  initialSymbol?: string;
};

export function StockSearch({
  initialSymbol = "",
}: StockSearchProps) {
  const router = useRouter();

  const [
    symbol,
    setSymbol,
  ] = useState(initialSymbol);

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const normalizedSymbol =
      symbol.trim().toUpperCase();

    if (!normalizedSymbol) {
      return;
    }

    router.push(
      `/stock/${encodeURIComponent(
        normalizedSymbol,
      )}`,
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full max-w-xl flex-col gap-3 sm:flex-row"
    >
      <label
        htmlFor="stock-symbol"
        className="sr-only"
      >
        Stock symbol
      </label>

      <input
        id="stock-symbol"
        type="text"
        value={symbol}
        onChange={(event) => {
          setSymbol(
            event.target.value,
          );
        }}
        placeholder="Enter symbol, e.g. AAPL"
        autoComplete="off"
        autoCapitalize="characters"
        maxLength={32}
        className="min-h-11 flex-1 rounded-xl border border-zinc-300 bg-white px-4 text-sm uppercase text-zinc-950 outline-none transition focus:border-zinc-500"
      />

      <button
        type="submit"
        className="min-h-11 rounded-xl bg-zinc-950 px-5 text-sm font-medium text-white transition hover:bg-zinc-800"
      >
        View stock
      </button>
    </form>
  );
}
