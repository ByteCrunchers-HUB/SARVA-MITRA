import { StyleSheet, Text, View } from "react-native";

import { colors, fonts, sizes, spacing } from "@/theme";

export function LiveBadge({
  label = "Live",
  tone = "live",
}: {
  label?: string;
  tone?: "live" | "pending";
}) {
  const pending = tone === "pending";
  return (
    <View style={[styles.wrap, pending && styles.wrapPending]}>
      <View style={[styles.dot, pending && styles.dotPending]} />
      <Text style={[styles.text, pending && styles.textPending]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: colors.greenSoft,
  },
  wrapPending: {
    backgroundColor: colors.amberSoft,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.green,
  },
  dotPending: {
    backgroundColor: colors.amber,
  },
  text: {
    color: colors.greenDeep,
    fontFamily: fonts.medium,
    fontSize: sizes.tiny,
    lineHeight: 14,
  },
  textPending: {
    color: colors.amberDark,
  },
});
