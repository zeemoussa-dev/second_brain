// `esm/`, not `lib/`: lib/core is CommonJS, and the Vite dev server hands its
// default import over as the module object, which React refuses to render.
import ReactEChartsCore from 'echarts-for-react/esm/core';
import { BarChart, LineChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import type { MonthRow } from './client';
import { formatMonth, usd } from './format';

echarts.use([BarChart, LineChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

/** A canvas cannot resolve `var(--x)`, so colours are read from the stylesheet
 *  when a chart renders. */
function cssColor(variable: string, fallback: string): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
  return value || fallback;
}

/** Revenue per month -- actual solid, forecast faded -- and the running total. */
export function RevenueChart({ rows, height = 300 }: { rows: MonthRow[]; height?: number }) {
  const actualColor = cssColor('--insight-series-actual', '#4c9be8');
  const forecastColor = cssColor('--insight-series-forecast', '#4c9be866');
  const lineColor = cssColor('--insight-series-cumulative', '#c58b5f');
  const muted = cssColor('--color-text-muted', '#b9b4a6');
  const border = cssColor('--color-border', 'rgba(233, 228, 214, 0.1)');
  const surface = cssColor('--color-surface-raised', '#1f2430');
  const text = cssColor('--color-text', '#e9e4d6');
  const option = {
    backgroundColor: 'transparent',
    textStyle: { color: muted, fontFamily: 'inherit' },
    grid: { left: 8, right: 8, top: 36, bottom: 8, containLabel: true },
    legend: { top: 0, left: 0, textStyle: { color: muted }, icon: 'roundRect', itemWidth: 12, itemHeight: 8 },
    tooltip: {
      trigger: 'axis', backgroundColor: surface, borderColor: border, textStyle: { color: text, fontSize: 12 },
      valueFormatter: (value: number) => usd(value),
    },
    xAxis: { type: 'category', data: rows.map((row) => formatMonth(row.month, true)),
             axisLabel: { color: muted }, axisLine: { lineStyle: { color: border } } },
    yAxis: [
      { type: 'value', axisLabel: { color: muted, formatter: (value: number) => usd(value, true) },
        splitLine: { lineStyle: { color: border } } },
      { type: 'value', axisLabel: { color: muted, formatter: (value: number) => usd(value, true) },
        splitLine: { show: false } },
    ],
    series: [
      { name: 'Actual', type: 'bar', stack: 'revenue', itemStyle: { color: actualColor },
        data: rows.map((row) => (row.kind === 'actual' ? row.revenue : null)) },
      { name: 'Forecast', type: 'bar', stack: 'revenue', itemStyle: { color: forecastColor },
        data: rows.map((row) => (row.kind === 'forecast' ? row.revenue : null)) },
      { name: 'Cumulative', type: 'line', yAxisIndex: 1, symbol: 'none', lineStyle: { color: lineColor },
        itemStyle: { color: lineColor }, data: rows.map((row) => row.cumulative ?? null) },
    ],
  };
  return (
    <div role="img" aria-label="Insight revenue by month">
      <ReactEChartsCore echarts={echarts} option={option} notMerge style={{ height, width: '100%' }} />
    </div>
  );
}
