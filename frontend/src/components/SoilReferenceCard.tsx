import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import type { SoilReference } from "@/data/soilSnapshot";
import { colors, fonts, radii, sizes, spacing } from "@/theme";
import { formatNumber } from "@/utils/format";

type SoilReferenceCardProps = {
  soil: SoilReference;
  compact?: boolean;
};

export function SoilReferenceCard({
  soil,
  compact = false,
}: SoilReferenceCardProps) {
  const items = [
    { label: "pH", value: formatNumber(soil.soil_ph, 1) },
    { label: "Organic C", value: `${formatNumber(soil.organic_carbon, 1)} g/kg` },
    { label: "Clay", value: `${formatNumber(soil.clay_pct, 1)}%` },
    { label: "Sand", value: `${formatNumber(soil.sand_pct, 1)}%` },
    { label: "Silt", value: `${formatNumber(soil.silt_pct, 1)}%` },
    { label: "Elevation", value: `${formatNumber(soil.elevation_m)} m` },
  ];

  return (
    <View style={styles.card}>
      <View style={styles.heading}>
        <Ionicons name="flask-outline" size={19} color={colors.greenDeep} />
        <Text style={styles.title}>Soil Reference</Text>
      </View>
      <View style={styles.grid}>
        {items.map((item) => (
          <View
            key={item.label}
            style={[styles.item, compact && styles.itemCompact]}
          >
            <Text style={styles.label}>{item.label}</Text>
            <Text style={styles.value}>{item.value}</Text>
          </View>
        ))}
      </View>
      <Text style={styles.note}>
        Nearest trained soil grid point. Not a lab soil test.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  heading: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h3,
    lineHeight: 24,
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
  },
  item: {
    width: "30%",
    minWidth: 92,
  },
  itemCompact: {
    width: "46%",
  },
  label: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.tiny,
    lineHeight: 16,
  },
  value: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.body,
    lineHeight: 22,
    marginTop: 2,
  },
  note: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
    marginTop: spacing.md,
  },
});
