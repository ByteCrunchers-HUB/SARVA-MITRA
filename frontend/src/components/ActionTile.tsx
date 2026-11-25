import { Ionicons } from "@expo/vector-icons";
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { colors, fonts, radii, sizes, spacing } from "@/theme";

type ActionTileProps = {
  icon: React.ComponentProps<typeof Ionicons>["name"];
  label: string;
  onPress: () => void;
  tint?: string;
  iconColor?: string;
};

export function ActionTile({
  icon,
  label,
  onPress,
  tint = colors.greenSoft,
  iconColor = colors.greenDeep,
}: ActionTileProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        { backgroundColor: tint },
        pressed && styles.pressed,
      ]}
    >
      <View style={styles.iconWrap}>
        <Ionicons name={icon} size={22} color={iconColor} />
      </View>
      <Text style={styles.label}>{label}</Text>
      <Ionicons
        name="chevron-forward"
        size={16}
        color={colors.textMuted}
        style={styles.chevron}
      />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: 116,
    borderRadius: radii.lg,
    padding: spacing.md,
    justifyContent: "space-between",
  },
  pressed: {
    opacity: 0.82,
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    color: colors.text,
    fontFamily: fonts.medium,
    fontSize: sizes.small,
    lineHeight: 19,
    maxWidth: "82%",
  },
  chevron: {
    position: "absolute",
    right: spacing.sm,
    bottom: spacing.sm,
  },
});
