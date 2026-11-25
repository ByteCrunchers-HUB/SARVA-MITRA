import { StyleSheet, Text, View } from "react-native";
import { Circle, Svg } from "react-native-svg";

import { colors, fonts, sizes } from "@/theme";
import { riskColor, riskLabel } from "@/utils/format";

type RiskGaugeProps = {
  pct: number | null;
  level?: string;
  size?: number;
};

export function RiskGauge({ pct, level, size = 190 }: RiskGaugeProps) {
  const stroke = 14;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const hasRisk = pct != null;
  const progress = hasRisk ? Math.max(0, Math.min(100, pct)) / 100 : 0;
  const accent = hasRisk ? riskColor(level) : colors.textMuted;

  return (
    <View style={[styles.root, { width: size, height: size }]}>
      <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={colors.border}
          strokeWidth={stroke}
          fill="none"
        />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={accent}
          strokeWidth={stroke}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - progress)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </Svg>
      <View style={styles.center}>
        <Text style={[styles.value, { color: accent }]}>
          {hasRisk ? `${Math.round(pct)}%` : "—"}
        </Text>
        <Text style={[styles.level, { color: accent }]}>
          {hasRisk ? riskLabel(level) : "No data"}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    alignItems: "center",
    justifyContent: "center",
  },
  center: {
    position: "absolute",
    alignItems: "center",
  },
  value: {
    fontFamily: fonts.bold,
    fontSize: 40,
    lineHeight: 48,
  },
  level: {
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
  },
});
