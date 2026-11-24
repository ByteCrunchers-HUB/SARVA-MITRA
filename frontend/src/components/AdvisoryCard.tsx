import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, fonts, radii, sizes, spacing } from "@/theme";

type AdvisoryCardProps = {
  text: string;
  onAskAssistant: () => void;
};

export function AdvisoryCard({ text, onAskAssistant }: AdvisoryCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.heading}>
        <View style={styles.iconWrap}>
          <Ionicons name="bulb-outline" size={20} color={colors.amberDark} />
        </View>
        <Text style={styles.title}>Quick Advisory</Text>
      </View>
      <Text style={styles.text}>{text}</Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Ask the AI assistant"
        onPress={onAskAssistant}
        style={({ pressed }) => [styles.link, pressed && styles.pressed]}
      >
        <Text style={styles.linkText}>Ask Assistant</Text>
        <Ionicons name="arrow-forward" size={14} color={colors.greenDeep} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.amberSoft,
    borderRadius: radii.lg,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: "#F6DFB6",
  },
  heading: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  iconWrap: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    color: colors.text,
    fontFamily: fonts.semibold,
    fontSize: sizes.body,
    lineHeight: 22,
  },
  text: {
    color: colors.textBody,
    fontFamily: fonts.regular,
    fontSize: sizes.small,
    lineHeight: 20,
  },
  link: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    alignSelf: "flex-start",
    marginTop: spacing.sm,
  },
  pressed: {
    opacity: 0.7,
  },
  linkText: {
    color: colors.greenDeep,
    fontFamily: fonts.semibold,
    fontSize: sizes.small,
    lineHeight: 19,
  },
});
