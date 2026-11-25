import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { colors, fonts, radii, shadows, sizes, spacing } from "@/theme";

type MetricTileProps = {
  icon: React.ComponentProps<typeof Ionicons>["name"];
  label: string;
  value: string;
  unit?: string;
  caption?: string;
  tint?: string;
  iconColor?: string;
};

export function MetricTile({
  icon,
  label,
  value,
  unit,
  caption,
  tint = colors.greenSoft,
  iconColor = colors.greenDeep,
}: MetricTileProps) {
  return (
    <View style={[styles.card, shadows.card]}>
      <View style={[styles.iconWrap, { backgroundColor: tint }]}>
        <Ionicons name={icon} size={20} color={iconColor} />
      </View>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.valueRow}>
        <Text style={styles.value}>{value}</Text>
        {unit ? <Text style={styles.unit}>{unit}</Text> : null}
      </View>
      {caption ? <Text style={styles.caption}>{caption}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: 134,
    backgroundColor: colors.card,
    borderRadius: radii.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  iconWrap: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.sm,
  },
  label: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.tiny,
    lineHeight: 16,
  },
  valueRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 3,
    marginTop: 2,
  },
  value: {
    color: colors.text,
    fontFamily: fonts.bold,
    fontSize: 21,
    lineHeight: 28,
  },
  unit: {
    color: colors.textMuted,
    fontFamily: fonts.medium,
    fontSize: sizes.tiny,
    lineHeight: 20,
    paddingBottom: 2,
  },
  caption: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: 10,
    lineHeight: 14,
    marginTop: 2,
  },
});
