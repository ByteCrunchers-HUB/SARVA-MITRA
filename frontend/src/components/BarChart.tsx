import { Rect, Svg, Text as SvgText } from "react-native-svg";

type BarChartProps = {
  values: number[];
  color?: string;
  height?: number;
  labels?: string[];
  unit?: string;
};

export function BarChart({
  values,
  color = "#4CAF50",
  height = 120,
  labels,
  unit = "",
}: BarChartProps) {
  if (values.length === 0) return null;

  const width = 320;
  const padding = 10;
  const max = Math.max(...values, 1);
  const slot = width / values.length;
  const barWidth = Math.min(30, slot * 0.52);
  const chartHeight = height - padding * 2;

  return (
    <Svg
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
    >
      {values.map((value, index) => {
        const barHeight = (value / max) * chartHeight;
        const x = index * slot + (slot - barWidth) / 2;
        const y = padding + (chartHeight - barHeight);
        return (
          <Rect
            key={`bar-${index}`}
            x={x}
            y={y}
            width={barWidth}
            height={Math.max(barHeight, 1)}
            rx={4}
            fill={color}
            fillOpacity={0.85}
          />
        );
      })}
      {values.map((value, index) => (
        <SvgText
          key={`label-${index}`}
          x={index * slot + slot / 2}
          y={height - 1}
          textAnchor="middle"
          fontSize={9}
          fill="#6F7D72"
        >
          {labels?.[index] ?? `${Math.round(value)}${unit}`}
        </SvgText>
      ))}
    </Svg>
  );
}
