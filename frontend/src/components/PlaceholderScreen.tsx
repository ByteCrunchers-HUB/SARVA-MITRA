import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { GreenHeader } from "@/components/GreenHeader";
import { Screen } from "@/components/Screen";
import { colors, fonts, sizes, spacing } from "@/theme";

type PlaceholderScreenProps = {
  title: string;
  subtitle: string;
  phase: string;
  icon?: React.ComponentProps<typeof Ionicons>["name"];
  showBack?: boolean;
};

export function PlaceholderScreen({
  title,
  subtitle,
  phase,
  icon = "construct-outline",
  showBack = false,
}: PlaceholderScreenProps) {
  return (
    <Screen
      edges={showBack ? ["left", "right", "bottom"] : ["left", "right"]}
    >
      <GreenHeader title={title} showBack={showBack} />
      <View style={styles.body}>
        <View style={styles.iconWrap}>
          <Ionicons name={icon} size={32} color={colors.greenDeep} />
        </View>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.subtitle}>{subtitle}</Text>
        <View style={styles.phasePill}>
          <Text style={styles.phaseText}>{phase}</Text>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.xxl,
    paddingBottom: spacing.xxxl,
  },
  iconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.greenSoft,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.lg,
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.h2,
    lineHeight: 28,
    textAlign: "center",
  },
  subtitle: {
    color: colors.textMuted,
    fontFamily: fonts.regular,
    fontSize: sizes.body,
    lineHeight: 22,
    textAlign: "center",
    marginTop: spacing.sm,
  },
  phasePill: {
    marginTop: spacing.xl,
    paddingHorizontal: spacing.md,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: colors.greenSoft,
  },
  phaseText: {
    color: colors.greenDeep,
    fontFamily: fonts.medium,
    fontSize: sizes.tiny,
    lineHeight: 16,
  },
});
