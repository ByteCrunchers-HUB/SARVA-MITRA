import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fonts, radii, sizes, spacing } from "@/theme";
import { riskColor, riskLabel, riskSoftColor } from "@/utils/format";

type RiskCardProps = {
  riskPct: number | null;
  riskLevel?: string;
  onPress?: () => void;
};

export function RiskCard({ riskPct, riskLevel, onPress }: RiskCardProps) {
  const hasRisk = riskPct != null;
  const tint = hasRisk ? riskSoftColor(riskLevel) : colors.card;
  const accent = hasRisk ? riskColor(riskLevel) : colors.textMuted;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="View crop risk details"
      disabled={!onPress}
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { backgroundColor: tint },
        pressed && onPress ? styles.pressed : null,
      ]}
    >
      <View style={[styles.iconWrap, { backgroundColor: `${accent}1A` }]}>
        <Ionicons name="shield-half-outline" size={24} color={accent} />
      </View>
      <View style={styles.copy}>
        <Text style={styles.label}>Crop Risk</Text>
        <View style={styles.valueRow}>
          <Text style={[styles.value, { color: accent }]}>
            {riskPct == null ? "—" : `${Math.round(riskPct)}%`}
          </Text>
          {riskPct == null ? (
            <View style={[styles.pill, styles.pillMuted]}>
              <Text style={[styles.pillText, styles.pillTextMuted]}>No data</Text>
            </View>
          ) : (
            <View style={[styles.pill, { backgroundColor: accent }]}>
              <Text style={styles.pillText}>{riskLabel(riskLevel)}</Text>
            </View>
          )}
        </View>
        <Text style={styles.caption}>Weather-based risk for the next day</Text>
      </View>
      {onPress ? (
        <View style={styles.link}>
          <Text style={[styles.linkText, { color: accent }]}>View Details</Text>
          <Ionicons name="arrow-forward" size={14} color={accent} />
        </View>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radii.lg,
    padding: spacing.md,
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  pressed: {
    opacity: 0.86,
  },
  iconWrap: {
    width: 46,
    height: 46,
    borderRadius: 23,
    alignItems: "center",
    justifyContent: "center",
  },
  copy: {
    flex: 1,
  },
  label: {
    color: colors.textBody,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
  },
  valueRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginTop: 1,
  },
  value: {
    fontFamily: fonts.bold,
    fontSize: 28,
    lineHeight: 36,
  },
  pill: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: 999,
  },
  pillMuted: {
    backgroundColor: colors.border,
  },
  pillText: {
    color: colors.white,
    fontFamily: fonts.semibold,
    fontSize: 10,
    lineHeight: 14,
  },
  pillTextMuted: {
    color: colors.textMuted,
  },
  caption: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
  },
  link: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    alignSelf: "flex-end",
  },
  linkText: {
    fontFamily: fonts.semibold,
    fontSize: 10,
    lineHeight: 14,
  },
});
