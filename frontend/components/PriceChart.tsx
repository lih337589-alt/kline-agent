"use client";

import {
  useEffect,
  useRef,
} from "react";
import * as echarts from "echarts";

import type {
  PriceRead,
} from "@/lib/api";

type PriceChartProps = {
  prices: PriceRead[];
};

export function PriceChart({
  prices,
}: PriceChartProps) {
  const containerRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container =
      containerRef.current;

    if (
      !container ||
      prices.length === 0
    ) {
      return;
    }

    const chart =
      echarts.init(container);

    const categories =
      prices.map(
        (price) =>
          price.timestamp.slice(
            0,
            10,
          ),
      );

    const candlestickData =
      prices.map(
        (price) => {
          const open =
            price.open ??
            price.close;

          const high =
            price.high ??
            Math.max(
              open,
              price.close,
            );

          const low =
            price.low ??
            Math.min(
              open,
              price.close,
            );

          return [
            open,
            price.close,
            low,
            high,
          ];
        },
      );

    const volumeData =
      prices.map(
        (price) =>
          price.volume ?? 0,
      );

    const option:
      echarts.EChartsOption = {
      animation: false,

      aria: {
        enabled: true,
      },

      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "cross",
        },
      },

      axisPointer: {
        link: [
          {
            xAxisIndex: "all",
          },
        ],
      },

      grid: [
        {
          left: "8%",
          right: "4%",
          top: "8%",
          height: "56%",
        },
        {
          left: "8%",
          right: "4%",
          top: "73%",
          height: "14%",
        },
      ],

      xAxis: [
        {
          type: "category",
          data: categories,
          boundaryGap: true,
          axisLine: {
            onZero: false,
          },
          min: "dataMin",
          max: "dataMax",
        },
        {
          type: "category",
          gridIndex: 1,
          data: categories,
          boundaryGap: true,
          axisLabel: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          min: "dataMin",
          max: "dataMax",
        },
      ],

      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true,
          },
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
        },
      ],

      dataZoom: [
        {
          type: "inside",
          xAxisIndex: [
            0,
            1,
          ],
          start: 40,
          end: 100,
        },
        {
          type: "slider",
          xAxisIndex: [
            0,
            1,
          ],
          bottom: "2%",
          start: 40,
          end: 100,
        },
      ],

      series: [
        {
          name: "Price",
          type: "candlestick",
          data: candlestickData,
          xAxisIndex: 0,
          yAxisIndex: 0,
        },
        {
          name: "Volume",
          type: "bar",
          data: volumeData,
          xAxisIndex: 1,
          yAxisIndex: 1,
        },
      ],
    };

    chart.setOption(option);

    function handleResize() {
      chart.resize();
    }

    window.addEventListener(
      "resize",
      handleResize,
    );

    return () => {
      window.removeEventListener(
        "resize",
        handleResize,
      );

      chart.dispose();
    };
  }, [prices]);

  if (prices.length === 0) {
    return (
      <div className="flex min-h-80 items-center justify-center rounded-2xl border border-dashed border-zinc-300 bg-white p-6">
        <p className="text-sm text-zinc-600">
          No price history is available.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="h-[520px] w-full"
      aria-label="Price and volume chart"
    />
  );
}
