import {
  Defs,
  LinearGradient,
  Path,
  Polyline,
  Stop,
  Svg,
} from "react-native-svg";

type SparklineProps = {
  values: number[];
  height?: number;
  color?: string;
  fillId?: string;
};

export function Sparkline({
  values,
  height = 72,
  color = "#4CAF50",
  fillId = "sparklineFill",
}: SparklineProps) {
  if (values.length < 2) return null;

  const width = 320;
  const padding = 8;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values.map((value, index) => {
    const x = (index / (values.length - 1)) * width;
    const y =
      height - padding - ((value - min) / range) * (height - padding * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const line = points.join(" ");
  const area = `M${points[0]} L${points.slice(1).join(" L")} L${width},${height} L0,${height} Z`;

  return (
    <Svg
      width="100%"
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
    >
      <Defs>
        <LinearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0%" stopColor={color} stopOpacity={0.28} />
          <Stop offset="100%" stopColor={color} stopOpacity={0} />
        </LinearGradient>
      </Defs>
      <Path d={area} fill={`url(#${fillId})`} />
      <Polyline
        points={line}
        fill="none"
        stroke={color}
        strokeWidth={2.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}
